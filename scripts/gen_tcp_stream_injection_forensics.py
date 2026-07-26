#!/usr/bin/env python3
"""Generate tcp-stream-injection-forensics task files."""
from __future__ import annotations

import json
import struct
import textwrap
import zlib
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tasks" / "tcp-stream-injection-forensics"
ENV = ROOT / "environment"
SPECS = Path(__file__).resolve().parents[1] / "specs"
OPT_ROOT = "/opt/wiretap"

CLIENT = "10.0.0.1"
SERVER = "10.0.0.2"
CPORT = 49152
SPORT = 8080


def w(rel: str, content: str) -> None:
    p = ROOT / rel if not rel.startswith("environment/") else ENV / rel.removeprefix("environment/")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")


def ip4(s: str) -> bytes:
    return bytes(int(x) for x in s.split("."))


def checksum(data: bytes) -> int:
    if len(data) % 2:
        data += b"\x00"
    s = sum(struct.unpack("!" + "H" * (len(data) // 2), data))
    while s >> 16:
        s = (s & 0xFFFF) + (s >> 16)
    return (~s) & 0xFFFF


def build_ip_tcp(
    src: str,
    dst: str,
    sport: int,
    dport: int,
    seq: int,
    ack: int,
    flags: int,
    window: int,
    payload: bytes,
    opts: bytes = b"",
) -> bytes:
    ihl = 5
    tcp_hdr_len = 20 + len(opts)
    total_len = 20 + tcp_hdr_len + len(payload)
    ip_hdr = struct.pack(
        "!BBHHHBBH4s4s",
        0x45,
        0,
        total_len,
        0,
        0,
        64,
        6,
        0,
        ip4(src),
        ip4(dst),
    )
    ip_hdr = ip_hdr[:10] + struct.pack("!H", checksum(ip_hdr)) + ip_hdr[12:]
    tcp = struct.pack("!HHIIHHHH", sport, dport, seq, ack, (tcp_hdr_len // 4) << 12, window, 0, 0)
    tcp = tcp + opts
    pseudo = ip4(src) + ip4(dst) + struct.pack("!BBH", 0, 6, tcp_hdr_len + len(payload))
    csum = checksum(pseudo + tcp + payload)
    tcp = tcp[:16] + struct.pack("!H", csum) + tcp[18:]
    return ip_hdr + tcp + payload


def eth_frame(ip_pkt: bytes, src_mac: bytes, dst_mac: bytes) -> bytes:
    return dst_mac + src_mac + b"\x08\x00" + ip_pkt


def write_pcap(path: Path, frames: list[tuple[float, bytes]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        f.write(struct.pack("<IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1))
        for ts, frame in frames:
            sec = int(ts)
            usec = int((ts - sec) * 1_000_000)
            f.write(struct.pack("<IIII", sec, usec, len(frame), len(frame)))
            f.write(frame)


MAC_C = bytes.fromhex("02:00:00:00:00:01".replace(":", ""))
MAC_S = bytes.fromhex("02:00:00:00:00:02".replace(":", ""))


@dataclass
class Seg:
    dir: str  # c2s or s2c
    seq: int
    payload: bytes
    ts: float
    window: int = 65535
    opts: bytes = b""


@dataclass
class FlowSpec:
    flow_id: str
    isn_c: int
    isn_s: int
    segments: list[Seg] = field(default_factory=list)


def sack_opt(left: int, right: int) -> bytes:
    # NOP NOP SACK left-right (one block)
    block = struct.pack("!II", left, right)
    sack = bytes([0x01, 0x01, 0x05, len(block) // 4]) + block
    pad = b"\x01" * ((4 - (len(sack) % 4)) % 4)
    return sack + pad


def relative_payloads(segs: list[Seg], isn_c: int, isn_s: int) -> list[Seg]:
    out: list[Seg] = []
    for s in segs:
        base = isn_c + 1 if s.dir == "c2s" else isn_s + 1
        out.append(Seg(s.dir, base + s.seq, s.payload, s.ts, s.window, s.opts))
    return out


def peer_south_deliver(segs: list[Seg]) -> tuple[bytes, list[list[int]], list[dict]]:
    """Server-side ingress for c2s."""
    if not segs:
        return b"", [], []
    ordered = sorted(segs, key=lambda s: (s.ts, s.seq))
    buf: dict[int, bytes] = {}
    first_seen: dict[tuple[int, int], bytes] = {}
    injected: list[list[int]] = []
    overlap_notes: list[dict] = []
    next_emit = min(s.seq for s in segs) if segs else 0

    def span_key(seq: int, data: bytes) -> tuple[int, int]:
        return seq, seq + len(data)

    for seg in ordered:
        key = span_key(seg.seq, seg.payload)
        if key in first_seen and first_seen[key] != seg.payload:
            prior = first_seen[key]
            start = seg.seq
            for i, (a, b) in enumerate(zip(prior, seg.payload)):
                if a != b:
                    rel = start + i - min(s.seq for s in segs)
                    injected.append([rel, rel + 1])
            continue
        if key not in first_seen:
            first_seen[key] = seg.payload
        # overlap merge: later ts wins
        for off in range(len(seg.payload)):
            pos = seg.seq + off
            if pos in buf:
                overlap_notes.append(
                    {"rel_off": pos - min(s.seq for s in segs), "dir": "c2s", "kept": "later"}
                )
            buf[pos] = seg.payload[off : off + 1]

    min_seq = min(s.seq for s in segs)
    max_seq = max(s.seq + len(s.payload) for s in segs)
    stream = bytearray()
    for pos in range(min_seq, max_seq):
        if pos not in buf:
            break
        stream.append(buf[pos][0])
        next_emit = pos + 1
    # trim to contiguous from min_seq
    out = bytearray()
    pos = min_seq
    while pos in buf:
        out.append(buf[pos][0])
        pos += 1
    return bytes(out), injected, overlap_notes


def peer_north_deliver(segs: list[Seg]) -> tuple[bytes, list[list[int]], list[dict]]:
    """Client-side ingress for s2c."""
    if not segs:
        return b"", [], []
    ordered = sorted(segs, key=lambda s: (s.ts, s.seq))
    buf: dict[int, bytes] = {}
    first_seen: dict[tuple[int, int], bytes] = {}
    injected: list[list[int]] = []
    overlap_notes: list[dict] = []

    for seg in ordered:
        key = (seg.seq, seg.seq + len(seg.payload))
        if key in first_seen and first_seen[key] != seg.payload:
            prior = first_seen[key]
            for i, (a, b) in enumerate(zip(prior, seg.payload)):
                if a != b:
                    rel = seg.seq + i - min(s.seq for s in segs)
                    injected.append([rel, rel + 1])
            # north keeps later on conflict
            for off, byte in enumerate(seg.payload):
                buf[seg.seq + off] = bytes([byte])
            continue
        if key not in first_seen:
            first_seen[key] = seg.payload
        for off in range(len(seg.payload)):
            pos = seg.seq + off
            if pos in buf:
                overlap_notes.append(
                    {"rel_off": pos - min(s.seq for s in segs), "dir": "s2c", "kept": "later"}
                )
            buf[pos] = seg.payload[off : off + 1]

    min_seq = min(s.seq for s in segs)
    out = bytearray()
    pos = min_seq
    while pos in buf:
        out.append(buf[pos][0])
        pos += 1
    return bytes(out), injected, overlap_notes


def peer_south_with_window(segs: list[Seg], shrink_at_ts: float, new_window: int) -> tuple[bytes, list[list[int]], list[dict]]:
    """Server ingress honoring window shrink after middlebox event."""
    ordered = sorted(segs, key=lambda s: (s.ts, s.seq))
    buf: dict[int, bytes] = {}
    if not segs:
        return b"", [], []
    rcv_nxt = min(s.seq for s in segs)
    base = rcv_nxt
    win = 65535
    for seg in ordered:
        if seg.ts >= shrink_at_ts:
            win = new_window
        if seg.seq + len(seg.payload) > rcv_nxt + win:
            continue
        for off in range(len(seg.payload)):
            buf[seg.seq + off] = seg.payload[off : off + 1]
        end = seg.seq + len(seg.payload)
        if end > rcv_nxt:
            rcv_nxt = end
    out = bytearray()
    pos = base
    while pos in buf:
        out.append(buf[pos][0])
        pos += 1
    return bytes(out), [], []


def build_flows() -> tuple[dict, dict]:
    flows: dict[str, FlowSpec] = {}
    truth: dict = {}

    # flow_alfa - reorder only
    alfa_c = b"GET /alfa HTTP/1.0\r\n\r\n"
    alfa_s = b"HTTP/1.0 200 OK\r\n\r\n"
    flows["flow_alfa"] = FlowSpec(
        "flow_alfa",
        1000,
        5000,
        [
            Seg("c2s", 0, alfa_c[:10], 1.0),
            Seg("c2s", 10, alfa_c[10:], 1.2),
            Seg("c2s", 0, alfa_c[:10], 0.8),  # duplicate earlier half
            Seg("s2c", 0, alfa_s, 1.5),
        ],
    )

    # flow_bravo - conflicting retrans on c2s
    bravo_good = b"POST /bravo SECRET=ABC123 HTTP/1.0\r\n\r\n"
    bravo_evil = b"POST /bravo SECRET=EVIL!! HTTP/1.0\r\n\r\n"
    flows["flow_bravo"] = FlowSpec(
        "flow_bravo",
        2000,
        6000,
        [
            Seg("c2s", 0, bravo_good, 1.0),
            Seg("c2s", 0, bravo_evil, 1.5),
            Seg("s2c", 0, b"HTTP/1.0 204 No Content\r\n\r\n", 2.0),
        ],
    )

    # flow_charlie - gap then fill on s2c
    charlie = b"ALPHA-GAP-BETA-CHUNK-END!!"
    flows["flow_charlie"] = FlowSpec(
        "flow_charlie",
        3000,
        7000,
        [
            Seg("c2s", 0, b"GET /charlie HTTP/1.0\r\n\r\n", 1.0),
            Seg("s2c", 0, charlie[:6], 1.1),
            Seg("s2c", 14, charlie[14:], 1.2),
            Seg("s2c", 6, charlie[6:14], 1.3),
        ],
    )

    # flow_delta - window shrink on c2s
    delta = b"PAYLOAD-DELTA-SEGMENT-XY"
    flows["flow_delta"] = FlowSpec(
        "flow_delta",
        4000,
        8000,
        [
            Seg("c2s", 0, delta[:8], 1.0, window=65535),
            Seg("c2s", 0, delta, 1.4, window=65535),
            Seg("c2s", 8, delta[8:], 1.5, window=65535),
        ],
    )

    for fid, spec in flows.items():
        rel = relative_payloads(spec.segments, spec.isn_c, spec.isn_s)
        c2s = [s for s in rel if s.dir == "c2s"]
        s2c = [s for s in rel if s.dir == "s2c"]
        if fid == "flow_delta":
            c2s_bytes, inj_c, ov_c = peer_south_with_window(c2s, shrink_at_ts=1.35, new_window=16)
        else:
            c2s_bytes, inj_c, ov_c = peer_south_deliver(c2s)
        s2c_bytes, inj_s, ov_s = peer_north_deliver(s2c)
        truth[fid] = {
            "c2s": c2s_bytes,
            "s2c": s2c_bytes,
            "c2s_injected": inj_c,
            "s2c_injected": inj_s,
            "overlap_notes": ov_c + ov_s,
            "c2s_len": len(c2s_bytes),
            "s2c_len": len(s2c_bytes),
        }

    return flows, truth


def flow_to_pcap(spec: FlowSpec) -> list[tuple[float, bytes]]:
    frames: list[tuple[float, bytes]] = []
    # SYN handshake minimal
    frames.append(
        (
            0.1,
            eth_frame(
                build_ip_tcp(CLIENT, SERVER, CPORT, SPORT, spec.isn_c, 0, 0x02, 8192, b""),
                MAC_C,
                MAC_S,
            ),
        )
    )
    frames.append(
        (
            0.2,
            eth_frame(
                build_ip_tcp(SERVER, CLIENT, SPORT, CPORT, spec.isn_s, spec.isn_c + 1, 0x12, 8192, b""),
                MAC_S,
                MAC_C,
            ),
        )
    )
    ack_c = spec.isn_c + 1
    ack_s = spec.isn_s + 1
    for seg in spec.segments:
        if seg.dir == "c2s":
            ip = build_ip_tcp(
                CLIENT,
                SERVER,
                CPORT,
                SPORT,
                spec.isn_c + 1 + seg.seq,
                ack_s,
                0x18,
                seg.window,
                seg.payload,
                seg.opts,
            )
            frames.append((seg.ts, eth_frame(ip, MAC_C, MAC_S)))
        else:
            ip = build_ip_tcp(
                SERVER,
                CLIENT,
                SPORT,
                CPORT,
                spec.isn_s + 1 + seg.seq,
                ack_c,
                0x18,
                seg.window,
                seg.payload,
                seg.opts,
            )
            frames.append((seg.ts, eth_frame(ip, MAC_S, MAC_C)))
    return frames


TRUTH: dict = {}


def write_specs() -> None:
    SPECS.mkdir(parents=True, exist_ok=True)
    w_spec = SPECS / "tcp-stream-injection-forensics.md"
    w_spec.write_text(
        textwrap.dedent(
            f"""
            ### Decision
            GO — Attempt 1. Original security forensics task on bidirectional byte delivery from captures; distributed Go fix path with opaque symbols.

            ### Metadata
            - version: 2
            - Task name: tcp-stream-injection-forensics
            - Title: TCP Stream Forensics
            - Category: security
            - Languages: ["go"]
            - Difficulty: hard
            - Codebase size: small
            - Subcategories: ["tool_specific"]
            - Tags: ["go", "pcap", "network", "forensics", "security", "tcp"]
            - Milestones: 0

            ## Authoring Brief

            ### Public contract
            Agent runs `{OPT_ROOT}/bin/wiretap analyze --manifest {OPT_ROOT}/data/manifest.json --out /output` after fixing the Go reassembly lane under `{OPT_ROOT}/`. For each flow in the manifest, write `/output/reassembled/<flow_id>_c2s.bin` and `/output/reassembled/<flow_id>_s2c.bin` containing the application bytes each endpoint delivered to userspace, plus `/output/findings.json` version 1 with per-flow `c2s_len`, `s2c_len`, half-open `[start,end)` `c2s_injected` and `s2c_injected` ranges relative to each delivered stream, and `overlap_notes` entries `{{rel_off, dir, kept}}` where `dir` is `c2s` or `s2c` and `kept` is `earlier` or `later`. Flow ids: `flow_alfa`, `flow_bravo`, `flow_charlie`, `flow_delta`.

            ### Failure topology
            Captures include reordering, duplicate spans with disagreeing octets, holes that close later, and a middlebox that shrinks the advertised window before smaller follow-on slices arrive. The stock analyzer concatenates capture order, ignores window clamping, never compares duplicate spans, and resolves overlaps by earliest timestamp. Symptoms: delivered streams disagree with peer notes, tamper ranges empty when duplicates differ, truncated `flow_delta` output.

            ### Environment shape
            Go module at `{OPT_ROOT}` with cmd entrypoint, internal packages for scan/stitch/queue/limit/challenge/emit, pkg helpers, manifest and captures under `{OPT_ROOT}/data`, peer docs under `{OPT_ROOT}/docs`, config under `{OPT_ROOT}/config`.

            ### Required artifacts
            instruction.md, task.toml, output_contract.toml, Dockerfile, .dockerignore, solve.sh, test.sh, test_outputs.py, 22+ environment files including Go sources, manifest, pcaps, peer docs, build script.

            ### Test plan
            - test_u1_alfa_c2s_bytes — byte-exact c2s for flow_alfa
            - test_k3_alfa_s2c_bytes — byte-exact s2c for flow_alfa
            - test_m8_bravo_c2s_keeps_first — bravo c2s resists tamper retrans
            - test_p2_bravo_injected_ranges — set equality on bravo c2s injected ranges
            - test_q5_charlie_s2c_gap — charlie s2c waits for hole fill
            - test_r7_delta_c2s_window — delta c2s respects shrink
            - test_s4_findings_schema — findings.json version and keys
            - test_t9_overlap_notes_alfa — overlap note present for alfa
            - test_h2_overlap_kept_alfa — overlap kept polarity for alfa c2s

            ### Drafting guardrails
            Symptoms-only instruction; no RFC names, no fix-path symbol names matching instruction nouns; expected bytes live in tests only.

            ### Triviality Ledger
            - Capture-order concat passes alfa reorder test but fails gap/window flows because queue and limit modules stay naive.
            - First-wins overlap passes alfa duplicates but fails bravo/s2c where peer docs specify later-wins paths.
            - Skipping payload compare yields empty injected ranges on bravo despite disagreeing duplicates on wire.

            ### Per-gate Pitfall Inventory
            - RC3: tests compare SHA256 of streams and injected set equality, not existence-only.
            - RC6: instruction describes symptoms and output schema, not stitch/queue/limit internals.
            - RC7: oracle rewrites four internal modules with substantive merge/drain/clamp/compare logic.
            - GX9: instruction names flow ids and field names, not per-byte expected payloads.
            - CR7: fix-path symbols use opaque k4/m2/p7/n5 names; no instruction noun substrings.

            ### Initial Draft Commitments
            - instruction.md
            - task.toml
            - output_contract.toml
            - environment/Dockerfile
            - environment/.dockerignore
            - environment/go.mod
            - environment/go.sum
            - environment/cmd/wiretap/main.go
            - environment/internal/scan/reader.go
            - environment/internal/scan/reader_test.go
            - environment/internal/k4/stitch.go
            - environment/internal/k4/hash.go
            - environment/internal/m2/queue.go
            - environment/internal/m2/slot.go
            - environment/internal/p7/limit.go
            - environment/internal/p7/clock.go
            - environment/internal/n5/challenge.go
            - environment/internal/n5/challenge_test.go
            - environment/internal/r8/emit.go
            - environment/pkg/lane/flow.go
            - environment/pkg/lane/flow_test.go
            - environment/config/lab.toml
            - environment/data/manifest.json
            - environment/data/build_captures.py
            - environment/data/captures/.gitkeep
            - environment/scripts/smoke.sh
            - solution/solve.sh
            - tests/test.sh
            - tests/test_outputs.py

            ### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

            #### symbol_table
            - path: internal/k4/stitch.go
              symbol: stitch
              kind: function
              signature: func stitch(buf map[int]byte, seq int, payload []byte, ts float64, preferLater bool) map[int]byte
              purpose: merge payload bytes into position map honoring overlap preference
            - path: internal/m2/queue.go
              symbol: drain
              kind: function
              signature: func drain(buf map[int]byte, start int) ([]byte, int)
              purpose: emit contiguous bytes from start while present
            - path: internal/p7/limit.go
              symbol: ceiling
              kind: function
              signature: func ceiling(rcvNxt int, win int, seq int, length int) bool
              purpose: return whether segment end fits inside receive window
            - path: internal/n5/challenge.go
              symbol: compare
              kind: function
              signature: func compare(a []byte, b []byte) (same bool, ranges [][2]int)
              purpose: detect byte ranges where two spans disagree

            #### flipping_point_contract
            locations:
              - id: A
                path: internal/k4/stitch.go
                controls_tests: [test_u1_alfa_c2s_bytes, test_m8_bravo_c2s_keeps_first, test_t9_overlap_notes_alfa]
              - id: B
                path: internal/m2/queue.go
                controls_tests: [test_q5_charlie_s2c_gap, test_k3_alfa_s2c_bytes]
              - id: C
                path: internal/p7/limit.go
                controls_tests: [test_r7_delta_c2s_window]
              - id: D
                path: internal/n5/challenge.go
                controls_tests: [test_p2_bravo_injected_ranges, test_m8_bravo_c2s_keeps_first]
            no_single_location_flips_majority: true
            concentration_cap: 0.5

            #### decoy_manifest
            - path: internal/k4/hash.go
              kind: helper
              rhymes_with: stitch
              non_fix_purpose: rolling fingerprint for manifest rows
            - path: internal/m2/slot.go
              kind: helper
              rhymes_with: drain
              non_fix_purpose: fixed-size slot pool for capture metadata
            - path: internal/p7/clock.go
              kind: helper
              rhymes_with: ceiling
              non_fix_purpose: capture timestamp normalization

            #### code_forbidden_tokens
            code_forbidden_tokens: [packet, capture, pcaps, tcp, sessions, application, protocol, segments, retransmissions, payloads, injection, endpoint, userspace, stream, flows, reassembled, findings, injected, ranges, delivered, overlap, decisions, forensics]
            """
        ).lstrip(),
        encoding="utf-8",
    )


def main() -> None:
    global TRUTH
    flows, TRUTH = build_flows()
    write_specs()

    # Captures generated into environment during docker build; embed truth for tests here
    truth_json = {
        fid: {
            "c2s_hex": v["c2s"].hex(),
            "s2c_hex": v["s2c"].hex(),
            "c2s_injected": v["c2s_injected"],
            "s2c_injected": v["s2c_injected"],
            "overlap_notes": v["overlap_notes"],
            "c2s_len": v["c2s_len"],
            "s2c_len": v["s2c_len"],
        }
        for fid, v in TRUTH.items()
    }

    w(
        "instruction.md",
        f"""
        Security review left several bidirectional conversation captures referenced by {OPT_ROOT}/data/manifest.json. The installed analyzer at {OPT_ROOT}/bin/wiretap should rebuild the application-layer byte streams each host actually handed to userspace and catalog forensic metadata from on-path gear replaying a span with different octets than an earlier copy.

        Current runs show scrambled delivery order, missing contested spans, short reads at sequence holes, overlap_notes missing for reordered client lanes, and client data accepted after a middlebox window shrink. Go sources live under {OPT_ROOT}/; rebuild the analyzer there and rerun.

        For each manifest flow id write /output/reassembled/<flow_id>_c2s.bin (client-to-server bytes the south endpoint delivered), /output/reassembled/<flow_id>_s2c.bin (server-to-client bytes the north endpoint delivered), and /output/findings.json. Do not modify capture files referenced by the manifest.

        findings.json uses version 1 at the top level and a flows section keyed by flow id. Each row reports c2s_len and s2c_len as delivered stream byte counts. Arrays c2s_injected and s2c_injected hold half-open start/end integer pairs naming stream-relative byte offsets where a later full-span replay disagreed with the body actually delivered on that lane. Array overlap_notes lists timestamp-ordered duplicate arrivals at byte offsets, including identical full-span replays whose timestamps disagree; each note carries rel_off (integer stream-relative offset), dir (c2s or s2c), and kept (earlier or later) naming which copy supplied the byte at that offset.

        Reassembly reads isn_client and isn_server from the manifest (stream-relative offsets subtract ISN plus one per direction) plus capture timestamps. Buffer out-of-order slices until the next sequence slot is present, then emit contiguous bytes in ascending order. wiretap analyze emits lane binaries and findings, then refreshes contested offsets and overlap_notes in findings.json from the captures.

        On the client-to-server lane, duplicate arrivals resolve to the later capture timestamp; record each affected offset in overlap_notes with dir c2s and kept later, even when the replay body matches byte-for-byte at the same sequence span. Full-span replays at the same sequence span with differing body octets keep the first body for delivery and list every disagreeing byte offset in c2s_injected. When window_shrink_ts and window_shrink_bytes appear in a manifest entry (for example flow_delta), reject c2s segments arriving at or after the shrink whose end sequence lies beyond rcv_nxt plus window_shrink_bytes measured at the shrink event.

        On the server-to-client lane, duplicate arrivals resolve to the later capture timestamp; record overlap_notes with dir s2c and kept later. Full-span replays with differing octets keep the later body for delivery and list disagreeing offsets in s2c_injected.

        Tampered client replays such as flow_bravo must record every contested byte offset in that flow's c2s_injected list with no extra phantom offsets. Rebuild the Go analyzer, then run wiretap analyze with the manifest path and an output directory under /output.
        """,
    )

    w(
        "task.toml",
        """
        version = "2.0"

        [metadata]
        author_name = "anonymous"
        author_email = "anonymous"
        difficulty = "hard"
        category = "security"
        subcategories = ["tool_specific"]
        number_of_milestones = 0
        codebase_size = "small"
        languages = ["go"]
        tags = ["go", "pcap", "network", "forensics", "security", "tcp"]
        expert_time_estimate_min = 120
        junior_time_estimate_min = 300

        [verifier]
        timeout_sec = 600

        [agent]
        timeout_sec = 1200

        [environment]
        allow_internet = false
        build_timeout_sec = 900
        cpus = 2
        memory_mb = 4096
        storage_mb = 10240
        """,
    )

    w(
        "output_contract.toml",
        f"""
        user_visible_outputs = [
          "/output/reassembled/<flow_id>_c2s.bin",
          "/output/reassembled/<flow_id>_s2c.bin",
          "/output/findings.json",
        ]

        internal_harness_files = [
          "{OPT_ROOT}/data/captures/",
        ]

        [structured_outputs.findings]
        target = "/output/findings.json"
        format = "json"
        instruction_checks = ["version", "flows", "c2s_injected", "s2c_injected", "overlap_notes"]
        """,
    )

    write_environment(flows, truth_json)
    write_tests(truth_json)
    write_solution()
    print(f"generated {ROOT}")


def write_environment(flows: dict, truth_json: dict) -> None:
    for stale in (
        ENV / "docs" / "peer_south.md",
        ENV / "docs" / "peer_north.md",
        ENV / "docs" / "capture_layout.md",
        ENV / "docs" / "lab_notes.txt",
        ENV / "config" / "reference.json",
        ENV / "internal" / "r8" / "reference.go",
    ):
        if stale.exists():
            stale.unlink()
    docs_dir = ENV / "docs"
    if docs_dir.is_dir() and not any(docs_dir.iterdir()):
        docs_dir.rmdir()
    manifest = {
        "version": 1,
        "flows": [
            {
                "id": fid,
                "capture": f"{OPT_ROOT}/data/captures/{fid}.pcap",
                "client": CLIENT,
                "server": SERVER,
                "client_port": CPORT,
                "server_port": SPORT,
                "isn_client": spec.isn_c,
                "isn_server": spec.isn_s,
                "window_shrink_ts": 1.35 if fid == "flow_delta" else None,
                "window_shrink_bytes": 16 if fid == "flow_delta" else None,
            }
            for fid, spec in flows.items()
        ],
    }
    w("environment/data/manifest.json", json.dumps(manifest, indent=2) + "\n")

    capture_py = Path(__file__).resolve().parent / "_tcp_capture_embed.py"
    capture_src = []
    for fid, spec in flows.items():
        frames = flow_to_pcap(spec)
        capture_src.append(f'    "{fid}": {repr(frames)},')
    capture_body = f'''#!/usr/bin/env python3
import struct
import os
from pathlib import Path

ROOT = Path(os.environ.get("CAPTURE_OUT", Path(__file__).resolve().parent / "captures"))
FLOWS = {{
{chr(10).join(capture_src)}
}}

def write_pcap(path, frames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        f.write(struct.pack("<IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1))
        for ts, frame in frames:
            sec = int(ts)
            usec = int((ts - sec) * 1_000_000)
            f.write(struct.pack("<IIII", sec, usec, len(frame), len(frame)))
            f.write(frame)

def main():
    for fid, frames in FLOWS.items():
        write_pcap(ROOT / f"{{fid}}.pcap", frames)

if __name__ == "__main__":
    main()
'''
    (ENV / "data" / "build_captures.py").write_text(capture_body, encoding="utf-8")

    w("environment/.dockerignore", """
.git
.gitignore
**/__pycache__/
**/*.pyc
**/.pytest_cache/
**/node_modules/
**/target/
**/dist/
**/build/
.env
*.log
bin/
wiretap
""")
    w(
        "environment/Dockerfile",
        f"""
        # syntax=docker/dockerfile:1

        # TB3 canonical runtime base: debian:bookworm-slim (pinned below).
        # Builder stage uses golang:1.24-bookworm because no Go image is listed
        # in the TB3 canonical base set yet; this task ships a prebuilt wiretap
        # binary and leaves the full module tree for agent-side rebuilds.

        FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

        WORKDIR /app
        COPY go.mod go.sum ./
        RUN go mod download
        COPY cmd/ ./cmd/
        COPY internal/ ./internal/
        COPY pkg/ ./pkg/
        RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/wiretap ./cmd/wiretap

        FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

        LABEL org.opencontainers.image.source="terminal-bench-3"
        LABEL org.opencontainers.image.version="1.0.0"
        LABEL org.opencontainers.image.licenses="MIT"

        # Agent session stack (tmux, asciinema) plus verifier runtime in one apt transaction.
        RUN apt-get update \\
            && apt-get install -y --no-install-recommends \\
                tmux \\
                asciinema \\
                bash \\
                ca-certificates \\
                coreutils \\
                procps \\
                python3 \\
                python3-pip \\
            && rm -rf /var/lib/apt/lists/*

        RUN pip3 install --no-cache-dir --break-system-packages \\
            pytest==8.4.1 \\
            pytest-json-ctrf==0.3.5

        ENV TERM=xterm-256color

        COPY --from=builder /usr/local/go /usr/local/go
        ENV PATH="/usr/local/go/bin:{OPT_ROOT}/bin:${{PATH}}" \\
            GOPATH=/go \\
            GOCACHE=/tmp/go-cache
        RUN mkdir -p /go /tmp/go-cache
        COPY --from=builder --chmod=755 /out/wiretap {OPT_ROOT}/bin/wiretap
        COPY cmd/ {OPT_ROOT}/cmd/
        COPY internal/ {OPT_ROOT}/internal/
        COPY pkg/ {OPT_ROOT}/pkg/
        COPY config/ {OPT_ROOT}/config/
        COPY go.mod go.sum {OPT_ROOT}/
        COPY data/manifest.json {OPT_ROOT}/data/manifest.json
        COPY data/build_captures.py /tmp/build_captures.py
        RUN mkdir -p {OPT_ROOT}/data/captures \\
            && CAPTURE_OUT={OPT_ROOT}/data/captures python3 /tmp/build_captures.py \\
            && rm /tmp/build_captures.py

        RUN tmux -V \\
            && asciinema --version \\
            && tmux new-session -d -s _smoke \\
            && tmux has-session -t _smoke \\
            && tmux kill-session -t _smoke

        WORKDIR {OPT_ROOT}
        """,
    )

    w(
        "environment/go.mod",
        """
        module lab.wiretap/app

        go 1.24
        """,
    )
    w("environment/go.sum", "")

    w("environment/config/lab.toml", f'tool = "wiretap"\nmanifest = "{OPT_ROOT}/data/manifest.json"\n')
    w("environment/config/paths.toml", f'root = "{OPT_ROOT}"\nmanifest = "{OPT_ROOT}/data/manifest.json"\n')

    w(
        "environment/scripts/smoke.sh",
        f"""
        #!/usr/bin/env bash
        set -euo pipefail
        {OPT_ROOT}/bin/wiretap analyze --manifest {OPT_ROOT}/data/manifest.json --out /tmp/smoke-out
        test -f /tmp/smoke-out/findings.json
        """,
    )

    w(
        "environment/cmd/wiretap/main.go",
        MAIN_GO,
    )
    w("environment/internal/scan/reader.go", READER_GO)
    w("environment/internal/scan/reader_test.go", READER_TEST_GO)
    w("environment/internal/k4/stitch.go", STITCH_BUG_GO)
    w("environment/internal/k4/south.go", SOUTH_GO)
    w("environment/internal/k4/hash.go", HASH_GO)
    w("environment/internal/m2/queue.go", QUEUE_BUG_GO)
    w("environment/internal/m2/slot.go", SLOT_GO)
    w("environment/internal/p7/limit.go", LIMIT_BUG_GO)
    w("environment/internal/p7/clock.go", CLOCK_GO)
    w("environment/internal/n5/challenge.go", CHALLENGE_BUG_GO)
    w("environment/internal/n5/challenge_test.go", CHALLENGE_TEST_GO)
    w("environment/internal/r8/inject.go", INJECT_GO)
    w("environment/internal/r8/verify_contract.go", CONTRACT_GO)
    w("environment/internal/r8/emit.go", EMIT_GO)
    w("environment/pkg/lane/flow.go", FLOW_GO)
    w("environment/pkg/lane/flow_test.go", FLOW_TEST_GO.replace("__OPT_ROOT__", OPT_ROOT))


def expected_rows(truth_json: dict) -> dict:
    import hashlib

    rows: dict = {}
    for fid, v in truth_json.items():
        c2s = bytes.fromhex(v["c2s_hex"])
        s2c = bytes.fromhex(v["s2c_hex"])
        rows[fid] = [
            hashlib.sha256(c2s).hexdigest(),
            hashlib.sha256(s2c).hexdigest(),
            len(c2s),
            len(s2c),
            v["c2s_injected"],
            v["s2c_injected"],
            sorted(n["rel_off"] for n in v["overlap_notes"] if n.get("dir") == "c2s"),
        ]
    return rows


def write_tests(truth_json: dict) -> None:
    w(
        "tests/test.sh",
        """
        #!/bin/bash

        mkdir -p /logs/verifier

        if [ "$PWD" = "/" ]; then
            echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
            echo 0 > /logs/verifier/reward.txt
            exit 1
        fi

        python3 -m pytest -o cache_dir=/tmp/pytest_cache \\
          --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA

        if [ $? -eq 0 ]; then
            echo 1 > /logs/verifier/reward.txt
        else
            echo 0 > /logs/verifier/reward.txt
        fi
        """,
    )

    expected = expected_rows(truth_json)

    body = f'''"""Verifier for wiretap forensic outputs."""

import json
import subprocess
from pathlib import Path

OUT = Path("/output")
REASM = OUT / "reassembled"
FINDINGS = OUT / "findings.json"
MANIFEST = Path("{OPT_ROOT}/data/manifest.json")

EXPECTED = json.loads({json.dumps(expected, indent=4)!r})

SHA_C2S = 0
SHA_S2C = 1
LEN_C2S = 2
LEN_S2C = 3
INJ_C2S = 4
INJ_S2C = 5
OVL_C2S = 6


def _flow_ids() -> list[str]:
    mf = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [row["id"] for row in mf["flows"]]


FLOWS = _flow_ids()


def _sha256(data: bytes) -> str:
    proc = subprocess.run(
        ["sha256sum"],
        input=data,
        capture_output=True,
        check=True,
    )
    return proc.stdout.decode().split()[0]


def _load_findings() -> dict:
    assert FINDINGS.is_file(), f"missing {{FINDINGS}}"
    doc = json.loads(FINDINGS.read_text(encoding="utf-8"))
    assert doc.get("version") == 1
    assert isinstance(doc.get("flows"), dict)
    return doc


def _covered_positions(ranges):
    pos = set()
    for start, end in ranges:
        for i in range(int(start), int(end)):
            pos.add(i)
    return pos


def _overlap_rel_offs(notes, direction):
    return {{n.get("rel_off") for n in notes if n.get("dir") == direction and n.get("rel_off") is not None}}


def test_binary_rebuilt():
    """wiretap analyze runs successfully after agent rebuild."""
    result = subprocess.run(
        [
            "{OPT_ROOT}/bin/wiretap",
            "analyze",
            "--manifest",
            str(MANIFEST),
            "--out",
            "/tmp/verify_out",
        ],
        capture_output=True,
    )
    assert result.returncode == 0


def test_n2_all_flow_artifacts_exist():
    """Each manifest flow emits lane binaries and a findings row."""
    doc = _load_findings()
    for fid in FLOWS:
        exp = EXPECTED[fid]
        c2s = REASM / f"{{fid}}_c2s.bin"
        s2c = REASM / f"{{fid}}_s2c.bin"
        assert c2s.is_file()
        assert s2c.is_file()
        if exp[LEN_C2S] > 0:
            assert c2s.stat().st_size > 0
        if exp[LEN_S2C] > 0:
            assert s2c.stat().st_size > 0
        assert fid in doc["flows"]


def test_u1_alfa_c2s_bytes():
    """flow_alfa client lane bytes match reconciled delivery."""
    fid = "flow_alfa"
    want = EXPECTED[fid][SHA_C2S]
    path = REASM / f"{{fid}}_c2s.bin"
    assert path.is_file()
    assert _sha256(path.read_bytes()) == want


def test_k3_alfa_s2c_bytes():
    """flow_alfa server lane bytes match reconciled delivery."""
    fid = "flow_alfa"
    want = EXPECTED[fid][SHA_S2C]
    path = REASM / f"{{fid}}_s2c.bin"
    assert path.is_file()
    assert _sha256(path.read_bytes()) == want
    doc = _load_findings()
    assert doc["flows"][fid]["s2c_len"] == path.stat().st_size


def test_m8_bravo_c2s_keeps_first():
    """flow_bravo client lane resists tampered resend bytes."""
    fid = "flow_bravo"
    want = EXPECTED[fid][SHA_C2S]
    path = REASM / f"{{fid}}_c2s.bin"
    assert _sha256(path.read_bytes()) == want


def test_p2_bravo_injected_ranges():
    """flow_bravo contested offsets match reconciled byte positions."""
    fid = "flow_bravo"
    exp = EXPECTED[fid]
    doc = _load_findings()
    got = doc["flows"][fid]["c2s_injected"]
    want = exp[INJ_C2S]
    assert len(got) > 0
    assert _covered_positions(got) == _covered_positions(want)


def test_q5_charlie_s2c_gap():
    """flow_charlie server lane waits for a late middle slice."""
    fid = "flow_charlie"
    want = EXPECTED[fid][SHA_S2C]
    path = REASM / f"{{fid}}_s2c.bin"
    assert _sha256(path.read_bytes()) == want
    doc = _load_findings()
    assert doc["flows"][fid]["s2c_len"] == EXPECTED[fid][LEN_S2C]


def test_r7_delta_c2s_window():
    """flow_delta client lane honors post-shrink accept window."""
    fid = "flow_delta"
    want = EXPECTED[fid][SHA_C2S]
    path = REASM / f"{{fid}}_c2s.bin"
    assert _sha256(path.read_bytes()) == want
    doc = _load_findings()
    assert doc["flows"][fid]["c2s_len"] == EXPECTED[fid][LEN_C2S]


def test_s4_findings_schema():
    """findings.json exposes required per-flow forensic fields."""
    doc = _load_findings()
    for fid in FLOWS:
        row = doc["flows"][fid]
        assert isinstance(row["c2s_len"], int)
        assert isinstance(row["s2c_len"], int)
        assert isinstance(row["c2s_injected"], list)
        assert isinstance(row["s2c_injected"], list)
        assert isinstance(row["overlap_notes"], list)
    assert len(doc["flows"]["flow_bravo"]["c2s_injected"]) > 0


def test_v4_s2c_injected_values():
    """each flow reports reconciled server-lane contested offsets."""
    doc = _load_findings()
    for fid in FLOWS:
        exp = EXPECTED[fid]
        got = doc["flows"][fid]["s2c_injected"]
        want = exp[INJ_S2C]
        assert _covered_positions(got) == _covered_positions(want)


def test_w6_reported_lengths_match_bins():
    """findings.json length fields match emitted binary sizes and contested catalog."""
    doc = _load_findings()
    for fid in FLOWS:
        row = doc["flows"][fid]
        assert row["c2s_len"] == (REASM / f"{{fid}}_c2s.bin").stat().st_size
        assert row["s2c_len"] == (REASM / f"{{fid}}_s2c.bin").stat().st_size
    bravo_inj = doc["flows"]["flow_bravo"]["c2s_injected"]
    assert isinstance(bravo_inj, list) and len(bravo_inj) > 0


def test_t9_overlap_notes_alfa():
    """flow_alfa records overlap resolution offsets on the client lane."""
    doc = _load_findings()
    got = doc["flows"]["flow_alfa"]["overlap_notes"]
    want_offs = set(EXPECTED["flow_alfa"][OVL_C2S])
    got_offs = _overlap_rel_offs(got, "c2s")
    assert got_offs == want_offs


def test_h2_overlap_kept_alfa():
    """flow_alfa overlap notes name which duplicate copy was kept."""
    doc = _load_findings()
    notes = [
        n
        for n in doc["flows"]["flow_alfa"]["overlap_notes"]
        if n.get("dir") == "c2s" and n.get("rel_off") is not None
    ]
    assert notes
    for note in notes:
        assert note.get("kept") == "later"
'''
    (ROOT / "tests" / "test_outputs.py").write_text(body, encoding="utf-8")
    row_ref = ROOT / "tests" / "row_ref.py"
    if row_ref.exists():
        row_ref.unlink()
    row_ref_env = ENV / "scripts" / "row_ref.py"
    if row_ref_env.exists():
        row_ref_env.unlink()


def write_solution() -> None:
    w(
        "solution/solve.sh",
        """
        #!/usr/bin/env bash
        set -euo pipefail

        cd __OPT_ROOT__

        cat > internal/k4/stitch.go <<'GOEOF'
        package k4

        func Stitch(buf map[int]byte, seq int, payload []byte, ts float64, preferLater bool) map[int]byte {
            if buf == nil {
                buf = make(map[int]byte)
            }
            meta := make(map[int]float64)
            for k := range buf {
                meta[k] = 0
            }
            for off := 0; off < len(payload); off++ {
                pos := seq + off
                if _, ok := buf[pos]; !ok {
                    buf[pos] = payload[off]
                    meta[pos] = ts
                    continue
                }
                if preferLater {
                    if ts >= meta[pos] {
                        buf[pos] = payload[off]
                        meta[pos] = ts
                    }
                } else if ts < meta[pos] || meta[pos] == 0 {
                    buf[pos] = payload[off]
                    meta[pos] = ts
                }
            }
            return buf
        }
        GOEOF

        cat > internal/m2/queue.go <<'GOEOF'
        package m2

        func Drain(buf map[int]byte, start int) ([]byte, int) {
            out := make([]byte, 0)
            pos := start
            for {
                b, ok := buf[pos]
                if !ok {
                    break
                }
                out = append(out, b)
                pos++
            }
            return out, pos
        }
        GOEOF

        cat > internal/p7/limit.go <<'GOEOF'
        package p7

        func Ceiling(rcvNxt int, win int, seq int, length int) bool {
            end := seq + length
            return end <= rcvNxt+win
        }
        GOEOF

        cat > internal/n5/challenge.go <<'GOEOF'
        package n5

        func Compare(a []byte, b []byte) (same bool, ranges [][2]int) {
            n := len(a)
            if len(b) < n {
                n = len(b)
            }
            same = len(a) == len(b)
            for i := 0; i < n; i++ {
                if a[i] != b[i] {
                    same = false
                    ranges = append(ranges, [2]int{i, i + 1})
                }
            }
            if len(a) != len(b) {
                same = false
            }
            return same, ranges
        }
        GOEOF

        cat > internal/r8/emit.go <<'GOEOF'
        package r8

        import (
            "encoding/json"
            "os"
            "path/filepath"
            "sort"

            "lab.wiretap/app/internal/m2"
            "lab.wiretap/app/internal/n5"
            "lab.wiretap/app/internal/p7"
            "lab.wiretap/app/internal/scan"
            "lab.wiretap/app/pkg/lane"
        )

        type note struct {
            RelOff int    `json:"rel_off"`
            Dir    string `json:"dir"`
            Kept   string `json:"kept"`
        }

        type row struct {
            C2SLen      int      `json:"c2s_len"`
            S2CLen      int      `json:"s2c_len"`
            C2SInjected [][2]int `json:"c2s_injected"`
            S2CInjected [][2]int `json:"s2c_injected"`
            Overlap     []note   `json:"overlap_notes"`
        }

        type doc struct {
            Version int            `json:"version"`
            Flows   map[string]row   `json:"flows"`
        }

        type span struct {
            seq int
            payload []byte
            ts float64
        }

        func relOff(abs int, base int) int { return abs - base }

        func assemble(segs []span, base int, preferLater bool, rejectLater bool, win int, shrinkTs float64, shrinkWin int) ([]byte, [][2]int, []note) {
            sort.Slice(segs, func(i, j int) bool {
                if segs[i].ts == segs[j].ts {
                    return segs[i].seq < segs[j].seq
                }
                return segs[i].ts < segs[j].ts
            })
            buf := map[int]byte{}
            meta := map[int]float64{}
            seen := map[[2]int][]byte{}
            injected := [][2]int{}
            notes := []note{}
            rcv := base
            if len(segs) > 0 {
                rcv = segs[0].seq
            }
            activeWin := win
            for _, seg := range segs {
                if shrinkTs > 0 && seg.ts >= shrinkTs {
                    activeWin = shrinkWin
                }
                if !p7.Ceiling(rcv, activeWin, seg.seq, len(seg.payload)) {
                    continue
                }
                key := [2]int{seg.seq, seg.seq + len(seg.payload)}
                if prior, ok := seen[key]; ok {
                    same, ranges := n5.Compare(prior, seg.payload)
                    if !same {
                        for _, rg := range ranges {
                            injected = append(injected, [2]int{relOff(seg.seq+rg[0], base), relOff(seg.seq+rg[1], base)})
                        }
                        if rejectLater {
                            continue
                        }
                    }
                } else {
                    seen[key] = append([]byte(nil), seg.payload...)
                }
                for off := 0; off < len(seg.payload); off++ {
                    pos := seg.seq + off
                    if _, ok := buf[pos]; ok {
                        kept := "later"
                        if !preferLater && seg.ts < meta[pos] {
                            kept = "earlier"
                        }
                        notes = append(notes, note{RelOff: relOff(pos, base), Dir: "", Kept: kept})
                    }
                    if preferLater {
                        if old, ok := meta[pos]; !ok || seg.ts >= old {
                            buf[pos] = seg.payload[off]
                            meta[pos] = seg.ts
                        }
                    } else if old, ok := meta[pos]; !ok || seg.ts < old || old == 0 {
                        buf[pos] = seg.payload[off]
                        meta[pos] = seg.ts
                    }
                }
                end := seg.seq + len(seg.payload)
                if end > rcv {
                    rcv = end
                }
            }
            out, _ := m2.Drain(buf, base)
            return out, injected, notes
        }

        func Analyze(manifestPath, outDir string) error {
            mf, err := lane.LoadManifest(manifestPath)
            if err != nil {
                return err
            }
            if err := os.MkdirAll(filepath.Join(outDir, "reassembled"), 0o755); err != nil {
                return err
            }
            flows := map[string]row{}
            for _, f := range mf.Flows {
                pkts, err := scan.ReadFile(f.Capture)
                if err != nil {
                    return err
                }
                c2s := []span{}
                s2c := []span{}
                cBase := f.ISNClient + 1
                sBase := f.ISNServer + 1
                for _, p := range pkts {
                    if p.PayloadLen == 0 {
                        continue
                    }
                    if p.Src == f.Client && p.Dst == f.Server && int(p.Sport) == f.ClientPort && int(p.Dport) == f.ServerPort {
                        c2s = append(c2s, span{seq: p.Seq, payload: append([]byte(nil), p.Payload...), ts: p.Ts})
                    }
                    if p.Src == f.Server && p.Dst == f.Client && int(p.Sport) == f.ServerPort && int(p.Dport) == f.ClientPort {
                        s2c = append(s2c, span{seq: p.Seq, payload: append([]byte(nil), p.Payload...), ts: p.Ts})
                    }
                }
                shrinkTs := 0.0
                shrinkWin := 65535
                if f.WindowShrinkTS != nil {
                    shrinkTs = *f.WindowShrinkTS
                }
                if f.WindowShrinkBytes != nil {
                    shrinkWin = *f.WindowShrinkBytes
                }
                cOut, cInj, cNotes := assemble(c2s, cBase, true, true, 65535, shrinkTs, shrinkWin)
                sOut, sInj, sNotes := assemble(s2c, sBase, true, false, 65535, 0, 65535)
                for i := range cNotes {
                    cNotes[i].Dir = "c2s"
                }
                for i := range sNotes {
                    sNotes[i].Dir = "s2c"
                }
                if err := os.WriteFile(filepath.Join(outDir, "reassembled", f.ID+"_c2s.bin"), cOut, 0o644); err != nil {
                    return err
                }
                if err := os.WriteFile(filepath.Join(outDir, "reassembled", f.ID+"_s2c.bin"), sOut, 0o644); err != nil {
                    return err
                }
                flows[f.ID] = row{
                    C2SLen: len(cOut), S2CLen: len(sOut),
                    C2SInjected: cInj, S2CInjected: sInj,
                    Overlap: append(cNotes, sNotes...),
                }
            }
            payload := doc{Version: 1, Flows: flows}
            raw, err := json.MarshalIndent(payload, "", "  ")
            if err != nil {
                return err
            }
            return os.WriteFile(filepath.Join(outDir, "findings.json"), raw, 0o644)
        }
        GOEOF

        python3 -c "from pathlib import Path; path=Path('internal/r8/inject.go'); text=path.read_text(encoding='utf-8'); old='for si, seg := range ordered {\\n        skipNotes := false\\n        for _, prior := range ordered[:si] {\\n            if prior.Seq == seg.Seq && prior.Ts < seg.Ts && bytes.Equal(prior.Payload, seg.Payload) {\\n                skipNotes = true\\n                break\\n            }\\n        }\\n        for off := 0; off < len(seg.Payload); off++ {\\n            pos := seg.Seq + off\\n            if _, ok := buf[pos]; ok && !skipNotes {'; new='for _, seg := range ordered {\\n        for off := 0; off < len(seg.Payload); off++ {\\n            pos := seg.Seq + off\\n            if _, ok := buf[pos]; ok {'; assert old in text, 'inject.go overlap skip anchor missing'; text=text.replace(old, new, 1); text=text.replace('    '+chr(34)+'bytes'+chr(34)+'\\n', '', 1); path.write_text(text, encoding='utf-8')"

        go build -o __OPT_ROOT__/bin/wiretap ./cmd/wiretap
        rm -rf /output
        mkdir -p /output
        __OPT_ROOT__/bin/wiretap analyze --manifest __OPT_ROOT__/data/manifest.json --out /output
        """.replace("__OPT_ROOT__", OPT_ROOT),
    )


MAIN_GO = '''
package main

import (
    "flag"
    "fmt"
    "os"

    "lab.wiretap/app/internal/r8"
)

func main() {
    if len(os.Args) < 2 {
        fmt.Fprintln(os.Stderr, "usage: wiretap analyze --manifest PATH --out DIR")
        os.Exit(2)
    }
    if os.Args[1] != "analyze" {
        fmt.Fprintln(os.Stderr, "unknown subcommand")
        os.Exit(2)
    }
    fs := flag.NewFlagSet("analyze", flag.ExitOnError)
    manifest := fs.String("manifest", "", "manifest path")
    out := fs.String("out", "", "output directory")
    _ = fs.Parse(os.Args[2:])
    if *manifest == "" || *out == "" {
        fmt.Fprintln(os.Stderr, "manifest and out required")
        os.Exit(2)
    }
    if err := r8.Analyze(*manifest, *out); err != nil {
        fmt.Fprintln(os.Stderr, err)
        os.Exit(1)
    }
    // Refresh contested offsets and overlap notes from captures into findings.json.
    if err := r8.AttachContested(*manifest, *out); err != nil {
        fmt.Fprintln(os.Stderr, err)
        os.Exit(1)
    }
}
'''

READER_GO = '''
package scan

import (
    "encoding/binary"
    "errors"
    "os"
)

type Packet struct {
    Ts         float64
    Src, Dst   string
    Sport, Dport uint16
    Seq        int
    Payload    []byte
    PayloadLen int
}

func ReadFile(path string) ([]Packet, error) {
    raw, err := os.ReadFile(path)
    if err != nil {
        return nil, err
    }
    if len(raw) < 24 {
        return nil, errors.New("short pcap")
    }
    var out []Packet
    off := 24
    for off+16 <= len(raw) {
        incl := int(binary.LittleEndian.Uint32(raw[off+8 : off+12]))
        sec := binary.LittleEndian.Uint32(raw[off : off+4])
        usec := binary.LittleEndian.Uint32(raw[off+4 : off+8])
        off += 16
        if off+incl > len(raw) {
            break
        }
        frame := raw[off : off+incl]
        off += incl
        if len(frame) < 14+20 {
            continue
        }
        ipOff := 14
        ihl := int(frame[ipOff]&0x0F) * 4
        if len(frame) < ipOff+ihl+20 {
            continue
        }
        src := ipToStr(frame[ipOff+12 : ipOff+16])
        dst := ipToStr(frame[ipOff+16 : ipOff+20])
        tcp := ipOff + ihl
        sport := binary.BigEndian.Uint16(frame[tcp : tcp+2])
        dport := binary.BigEndian.Uint16(frame[tcp+2 : tcp+4])
        seq := int(binary.BigEndian.Uint32(frame[tcp+4 : tcp+8]))
        dataOff := int(frame[tcp+12]>>4) * 4
        payload := frame[tcp+dataOff:]
        out = append(out, Packet{
            Ts: float64(sec) + float64(usec)/1e6,
            Src: src, Dst: dst,
            Sport: sport, Dport: dport,
            Seq: seq,
            Payload: payload,
            PayloadLen: len(payload),
        })
    }
    return out, nil
}

func ipToStr(b []byte) string {
    return fmtIP(b[0], b[1], b[2], b[3])
}

func fmtIP(a, b, c, d byte) string {
    buf := make([]byte, 0, 15)
    buf = appendInt(buf, a)
    buf = append(buf, '.')
    buf = appendInt(buf, b)
    buf = append(buf, '.')
    buf = appendInt(buf, c)
    buf = append(buf, '.')
    buf = appendInt(buf, d)
    return string(buf)
}

func appendInt(buf []byte, v byte) []byte {
    if v >= 100 {
        buf = append(buf, '0'+v/100)
        v %= 100
        buf = append(buf, '0'+v/10)
        return append(buf, '0'+v%10)
    }
    if v >= 10 {
        buf = append(buf, '0'+v/10)
        return append(buf, '0'+v%10)
    }
    return append(buf, '0'+v)
}
'''

READER_TEST_GO = '''
package scan

import "testing"

func TestFmtIP(t *testing.T) {
    if fmtIP(10, 0, 0, 1) != "10.0.0.1" {
        t.Fatal("ip fmt")
    }
}
'''

STITCH_BUG_GO = '''
package k4

func Stitch(buf map[int]byte, seq int, payload []byte, ts float64, preferLater bool) map[int]byte {
    if buf == nil {
        buf = make(map[int]byte)
    }
    for off := 0; off < len(payload); off++ {
        pos := seq + off
        if _, ok := buf[pos]; ok {
            continue
        }
        buf[pos] = payload[off]
    }
    return buf
}
'''

SOUTH_GO = '''
package k4

import (
    "bytes"
    "sort"
)

type SouthSeg struct {
    Seq     int
    Payload []byte
    Ts      float64
}

func SouthMerge(segs []SouthSeg) map[int]byte {
    ordered := append([]SouthSeg(nil), segs...)
    sort.Slice(ordered, func(i, j int) bool {
        if ordered[i].Ts == ordered[j].Ts {
            return ordered[i].Seq < ordered[j].Seq
        }
        return ordered[i].Ts < ordered[j].Ts
    })
    seen := map[[2]int][]byte{}
    buf := map[int]byte{}
    meta := map[int]float64{}
    for _, seg := range ordered {
        key := [2]int{seg.Seq, seg.Seq + len(seg.Payload)}
        if prior, ok := seen[key]; ok {
            if !bytes.Equal(prior, seg.Payload) {
                continue
            }
        } else {
            seen[key] = append([]byte(nil), seg.Payload...)
        }
        for off := 0; off < len(seg.Payload); off++ {
            pos := seg.Seq + off
            if old, ok := meta[pos]; !ok || seg.Ts >= old {
                buf[pos] = seg.Payload[off]
                meta[pos] = seg.Ts
            }
        }
    }
    return buf
}
'''

HASH_GO = '''
package k4

func rolling(data []byte) uint32 {
    var h uint32 = 2166136261
    for _, b := range data {
        h ^= uint32(b)
        h *= 16777619
    }
    return h
}
'''

QUEUE_BUG_GO = '''
package m2

func Drain(buf map[int]byte, start int) ([]byte, int) {
    return nil, start
}
'''

SLOT_GO = '''
package m2

type Slot struct {
    ID int
    Used bool
}

func NewPool(n int) []Slot {
    s := make([]Slot, n)
    for i := range s {
        s[i] = Slot{ID: i}
    }
    return s
}
'''

LIMIT_BUG_GO = '''
package p7

func Ceiling(rcvNxt int, win int, seq int, length int) bool {
    _ = rcvNxt
    _ = win
    _ = seq
    _ = length
    return true
}
'''

CLOCK_GO = '''
package p7

func Normalize(ts float64) float64 {
    return ts
}
'''

CHALLENGE_BUG_GO = '''
package n5

func Compare(a []byte, b []byte) (same bool, ranges [][2]int) {
    _ = a
    _ = b
    return true, nil
}
'''

CHALLENGE_TEST_GO = '''
package n5

import "testing"

func TestCompareDefault(t *testing.T) {
    same, ranges := Compare([]byte("a"), []byte("b"))
    if !same || ranges != nil {
        t.Fatal("default compare path")
    }
}

func TestCompareContestedReplay(t *testing.T) {
    good := []byte("POST /bravo SECRET=ABC123 HTTP/1.0\\r\\n\\r\\n")
    evil := []byte("POST /bravo SECRET=EVIL!! HTTP/1.0\\r\\n\\r\\n")
    same, ranges := Compare(good, evil)
    if same || len(ranges) == 0 {
        t.Fatal("compare should list contested byte offsets for disagreeing replays")
    }
}
'''

EMIT_GO = '''
package r8

import (
    "encoding/json"
    "os"
    "path/filepath"
    "lab.wiretap/app/internal/k4"
    "lab.wiretap/app/internal/m2"
    "lab.wiretap/app/internal/p7"
    "lab.wiretap/app/internal/scan"
    "lab.wiretap/app/pkg/lane"
)

type note struct {
    RelOff int    `json:"rel_off"`
    Dir    string `json:"dir"`
    Kept   string `json:"kept"`
}

type row struct {
    C2SLen      int      `json:"c2s_len"`
    S2CLen      int      `json:"s2c_len"`
    C2SInjected [][2]int `json:"c2s_injected"`
    S2CInjected [][2]int `json:"s2c_injected"`
    Overlap     []note   `json:"overlap_notes"`
}

type doc struct {
    Version int          `json:"version"`
    Flows   map[string]row `json:"flows"`
}

type span struct {
    seq     int
    payload []byte
    ts      float64
}

func laneSegs(segs []span) []LaneSeg {
    out := make([]LaneSeg, len(segs))
    for i, s := range segs {
        out[i] = LaneSeg{Seq: s.seq, Payload: s.payload}
    }
    return out
}

func southSegs(segs []span) []k4.SouthSeg {
    out := make([]k4.SouthSeg, len(segs))
    for i, s := range segs {
        out[i] = k4.SouthSeg{Seq: s.seq, Payload: s.payload, Ts: s.ts}
    }
    return out
}

func Analyze(manifestPath, outDir string) error {
    mf, err := lane.LoadManifest(manifestPath)
    if err != nil {
        return err
    }
    if err := os.MkdirAll(filepath.Join(outDir, "reassembled"), 0o755); err != nil {
        return err
    }
    flows := map[string]row{}
    for _, f := range mf.Flows {
        pkts, err := scan.ReadFile(f.Capture)
        if err != nil {
            return err
        }
        c2s := []span{}
        s2c := []span{}
        cBase := f.ISNClient + 1
        sBase := f.ISNServer + 1
        for _, p := range pkts {
            if p.PayloadLen == 0 {
                continue
            }
            if p.Src == f.Client && p.Dst == f.Server && int(p.Sport) == f.ClientPort && int(p.Dport) == f.ServerPort {
                c2s = append(c2s, span{seq: p.Seq, payload: append([]byte(nil), p.Payload...), ts: p.Ts})
            }
            if p.Src == f.Server && p.Dst == f.Client && int(p.Sport) == f.ServerPort && int(p.Dport) == f.ClientPort {
                s2c = append(s2c, span{seq: p.Seq, payload: append([]byte(nil), p.Payload...), ts: p.Ts})
            }
        }
        cBuf := k4.SouthMerge(southSegs(c2s))
        sBuf := map[int]byte{}
        for _, s := range s2c {
            sBuf = k4.Stitch(sBuf, s.seq, s.payload, s.ts, true)
        }
        cOut, _ := m2.Drain(cBuf, cBase)
        sOut, _ := m2.Drain(sBuf, sBase)
        cInj := ContestedOffsets(laneSegs(c2s), cBase)
        sInj := ContestedOffsets(laneSegs(s2c), sBase)
        cTimed := make([]timedLaneSeg, len(c2s))
        for i, s := range c2s {
            cTimed[i] = timedLaneSeg{Seq: s.seq, Payload: append([]byte(nil), s.payload...), Ts: s.ts}
        }
        sTimed := make([]timedLaneSeg, len(s2c))
        for i, s := range s2c {
            sTimed[i] = timedLaneSeg{Seq: s.seq, Payload: append([]byte(nil), s.payload...), Ts: s.ts}
        }
        overlap := append(
            LaneOverlapNotes(cTimed, cBase, "c2s", true),
            LaneOverlapNotes(sTimed, sBase, "s2c", true)...,
        )
        _ = p7.Ceiling(0, 0, 0, 0)
        if err := os.WriteFile(filepath.Join(outDir, "reassembled", f.ID+"_c2s.bin"), cOut, 0o644); err != nil {
            return err
        }
        if err := os.WriteFile(filepath.Join(outDir, "reassembled", f.ID+"_s2c.bin"), sOut, 0o644); err != nil {
            return err
        }
        flows[f.ID] = row{
            C2SLen: len(cOut) + 1, S2CLen: len(sOut) + 1,
            C2SInjected: cInj, S2CInjected: sInj,
            Overlap: overlap,
        }
    }
    payload := doc{Version: 1, Flows: flows}
    raw, err := json.MarshalIndent(payload, "", "  ")
    if err != nil {
        return err
    }
    return os.WriteFile(filepath.Join(outDir, "findings.json"), raw, 0o644)
}
'''

CONTRACT_GO = '''
package r8

// OverlapNote records duplicate-arrival resolution, including identical full-span replays.
type OverlapNote struct {
    RelOff int    `json:"rel_off"`
    Dir    string `json:"dir"`
    Kept   string `json:"kept"`
}

// VerifyContractRow documents reconciled lane metadata checked by external verification.
type VerifyContractRow struct {
    C2SLen      int           `json:"c2s_len"`
    S2CLen      int           `json:"s2c_len"`
    C2SInjected [][2]int      `json:"c2s_injected"`
    S2CInjected [][2]int      `json:"s2c_injected"`
    OverlapNotes []OverlapNote `json:"overlap_notes"`
}
'''

INJECT_GO = '''
package r8

import (
    "bytes"
    "encoding/json"
    "os"
    "path/filepath"
    "sort"

    "lab.wiretap/app/internal/scan"
    "lab.wiretap/app/pkg/lane"
)

type LaneSeg struct {
    Seq     int
    Payload []byte
}

type timedLaneSeg struct {
    Seq     int
    Payload []byte
    Ts      float64
}

type contestedRow struct {
    C2SLen      int      `json:"c2s_len"`
    S2CLen      int      `json:"s2c_len"`
    C2SInjected [][2]int `json:"c2s_injected"`
    S2CInjected [][2]int `json:"s2c_injected"`
    Overlap     []note   `json:"overlap_notes"`
}

type contestedDoc struct {
    Version int                     `json:"version"`
    Flows   map[string]contestedRow `json:"flows"`
}

func disagreeRanges(a, b []byte) [][2]int {
    n := len(a)
    if len(b) < n {
        n = len(b)
    }
    out := [][2]int{}
    for i := 0; i < n; i++ {
        if a[i] != b[i] {
            out = append(out, [2]int{i, i + 1})
        }
    }
    return out
}

func ContestedOffsets(segs []LaneSeg, base int) [][2]int {
    seen := map[[2]int][]byte{}
    injected := [][2]int{}
    for _, s := range segs {
        if len(s.Payload) == 0 {
            continue
        }
        key := [2]int{s.Seq, s.Seq + len(s.Payload)}
        if prior, ok := seen[key]; ok {
            for _, rg := range disagreeRanges(prior, s.Payload) {
                injected = append(injected, [2]int{s.Seq + rg[0] - base, s.Seq + rg[1] - base})
            }
        } else {
            seen[key] = append([]byte(nil), s.Payload...)
        }
    }
    return injected
}

func LaneOverlapNotes(segs []timedLaneSeg, base int, dir string, preferLater bool) []note {
    if len(segs) == 0 {
        return nil
    }
    ordered := append([]timedLaneSeg(nil), segs...)
    sort.Slice(ordered, func(i, j int) bool {
        if ordered[i].Ts == ordered[j].Ts {
            return ordered[i].Seq < ordered[j].Seq
        }
        return ordered[i].Ts < ordered[j].Ts
    })
    buf := map[int]byte{}
    meta := map[int]float64{}
    notes := []note{}
    for si, seg := range ordered {
        skipNotes := false
        for _, prior := range ordered[:si] {
            if prior.Seq == seg.Seq && prior.Ts < seg.Ts && bytes.Equal(prior.Payload, seg.Payload) {
                skipNotes = true
                break
            }
        }
        for off := 0; off < len(seg.Payload); off++ {
            pos := seg.Seq + off
            if _, ok := buf[pos]; ok && !skipNotes {
                kept := "later"
                if !preferLater {
                    kept = "earlier"
                }
                notes = append(notes, note{RelOff: pos - base, Dir: dir, Kept: kept})
            }
            if preferLater {
                if old, ok := meta[pos]; !ok || seg.Ts >= old {
                    buf[pos] = seg.Payload[off]
                    meta[pos] = seg.Ts
                }
            } else if old, ok := meta[pos]; !ok || seg.Ts < old || old == 0 {
                buf[pos] = seg.Payload[off]
                meta[pos] = seg.Ts
            }
        }
    }
    return notes
}

func flowTimedLaneSegs(f lane.Flow) (c2s []timedLaneSeg, s2c []timedLaneSeg, cBase int, sBase int, err error) {
    pkts, err := scan.ReadFile(f.Capture)
    if err != nil {
        return nil, nil, 0, 0, err
    }
    cBase = f.ISNClient + 1
    sBase = f.ISNServer + 1
    for _, p := range pkts {
        if p.PayloadLen == 0 {
            continue
        }
        if p.Src == f.Client && p.Dst == f.Server && int(p.Sport) == f.ClientPort && int(p.Dport) == f.ServerPort {
            c2s = append(c2s, timedLaneSeg{Seq: p.Seq, Payload: append([]byte(nil), p.Payload...), Ts: p.Ts})
        }
        if p.Src == f.Server && p.Dst == f.Client && int(p.Sport) == f.ServerPort && int(p.Dport) == f.ClientPort {
            s2c = append(s2c, timedLaneSeg{Seq: p.Seq, Payload: append([]byte(nil), p.Payload...), Ts: p.Ts})
        }
    }
    return c2s, s2c, cBase, sBase, nil
}

func flowLaneSegs(f lane.Flow) (c2s []LaneSeg, s2c []LaneSeg, cBase int, sBase int, err error) {
    cTimed, sTimed, cBase, sBase, err := flowTimedLaneSegs(f)
    if err != nil {
        return nil, nil, 0, 0, err
    }
    for _, s := range cTimed {
        c2s = append(c2s, LaneSeg{Seq: s.Seq, Payload: s.Payload})
    }
    for _, s := range sTimed {
        s2c = append(s2c, LaneSeg{Seq: s.Seq, Payload: s.Payload})
    }
    return c2s, s2c, cBase, sBase, nil
}

func AttachContested(manifestPath, outDir string) error {
    findingsPath := filepath.Join(outDir, "findings.json")
    raw, err := os.ReadFile(findingsPath)
    if err != nil {
        return err
    }
    var payload contestedDoc
    if err := json.Unmarshal(raw, &payload); err != nil {
        return err
    }
    mf, err := lane.LoadManifest(manifestPath)
    if err != nil {
        return err
    }
    for _, f := range mf.Flows {
        c2s, s2c, cBase, sBase, err := flowTimedLaneSegs(f)
        if err != nil {
            return err
        }
        row, ok := payload.Flows[f.ID]
        if !ok {
            row = contestedRow{}
        }
        plainC2S := make([]LaneSeg, len(c2s))
        plainS2C := make([]LaneSeg, len(s2c))
        for i, s := range c2s {
            plainC2S[i] = LaneSeg{Seq: s.Seq, Payload: s.Payload}
        }
        for i, s := range s2c {
            plainS2C[i] = LaneSeg{Seq: s.Seq, Payload: s.Payload}
        }
        row.C2SInjected = ContestedOffsets(plainC2S, cBase)
        row.S2CInjected = ContestedOffsets(plainS2C, sBase)
        row.Overlap = append(
            LaneOverlapNotes(c2s, cBase, "c2s", true),
            LaneOverlapNotes(s2c, sBase, "s2c", true)...,
        )
        payload.Flows[f.ID] = row
    }
    out, err := json.MarshalIndent(payload, "", "  ")
    if err != nil {
        return err
    }
    return os.WriteFile(findingsPath, out, 0o644)
}
'''

FLOW_GO = '''
package lane

import (
    "encoding/json"
    "os"
)

type Flow struct {
    ID                 string   `json:"id"`
    Capture            string   `json:"capture"`
    Client             string   `json:"client"`
    Server             string   `json:"server"`
    ClientPort         int      `json:"client_port"`
    ServerPort         int      `json:"server_port"`
    ISNClient          int      `json:"isn_client"`
    ISNServer          int      `json:"isn_server"`
    WindowShrinkTS     *float64 `json:"window_shrink_ts"`
    // WindowShrinkBytes is receive-window size beyond rcv_nxt after WindowShrinkTS.
    WindowShrinkBytes  *int     `json:"window_shrink_bytes"`
}

type Manifest struct {
    Version int    `json:"version"`
    Flows   []Flow `json:"flows"`
}

func LoadManifest(path string) (*Manifest, error) {
    raw, err := os.ReadFile(path)
    if err != nil {
        return nil, err
    }
    var mf Manifest
    if err := json.Unmarshal(raw, &mf); err != nil {
        return nil, err
    }
    return &mf, nil
}
'''

FLOW_TEST_GO = '''
package lane

import "testing"

func TestManifestVersion(t *testing.T) {
    mf, err := LoadManifest("__OPT_ROOT__/data/manifest.json")
    if err != nil {
        t.Skip("manifest not present in unit env")
    }
    if mf.Version != 1 {
        t.Fatalf("version %d", mf.Version)
    }
}
'''


if __name__ == "__main__":
    main()
