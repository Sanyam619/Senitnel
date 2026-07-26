"""Verifier for the columnar compaction rewind reconstruction.

Every expected value is recomputed from the pinned input fixtures under
/app/data; nothing is trusted from agent-writable locations. The pin check
guards the recomputation against fixture tampering.
"""

import hashlib
import json
from pathlib import Path

DATA = Path("/app/data")
REPORT = Path("/output/rewind-report.json")
VIEW_DIR = Path("/output/view")

INPUT_PINS = {
    "columns/events_001.col": "42b9673df6f6bbaf9d21d3bcef0f635bc59c9171376c95a696635236984fd684",
    "columns/events_002.col": "1dfb136b2490db8c100fff2d0f66d99b1640137ca2ac803fdccdd2b3a37d98d9",
    "columns/events_003.col": "b9672052ce0f7e523faf55d3d86c8ff66ca986dbbefb95a4c2d3dfb7d4f9b13f",
    "columns/events_004.col": "208fbaf58952dc89b5459a80d0c4acab7a3182447a9919b21950e2413d7dd2a8",
    "columns/events_merged.col": "60606f5213aa290f1e77b263e6f694085786a1ebe235a003ed937a8ed8f74aa3",
    "columns/metrics_010.col": "40aad644beab49dfbb023519d259e116fa9a660847a7bc9ebae29aa0e34ab47e",
    "columns/metrics_011.col": "d8551f6d4dcd0bb012d5699c24099186cb3d7722c87fd9a2c974f6a9d1622d6e",
    "columns/metrics_012.col": "527e2c138204542f8d134a3179d951b05c07e45d8085252bbdeca6bb5e2068a4",
    "columns/metrics_merged.col": "ac655d7dd31fd2194aa810dc717160a64c4813432257c02feaab44e11e70e4fc",
    "manifests/tier_a.jsonl": "b9c546ed152e5eff0bd94d9207dc5eaebc1c3800629e5b45d880f228461223fa",
    "manifests/tier_b.jsonl": "b85fb93376ef522ce832e62303a3bc78fa9650f15bc42f9dd655144cf8835ff2",
    "manifests/tier_c.jsonl": "4973957db7de38100253261a34168c7665eccc308e8c2a29f385206c6d4f3d5b",
    "sidecars/events.idx": "8756eabb732a9eb30a78de63537a2d7011dbba3964f4f7ae7bbc96f850635fae",
    "sidecars/metrics.idx": "8a8c484133906e7b6b0a7d0580b007de906dc259139fce17f530637b220c1dc2",
    "state/last_boot.json": "bc13ae9d317c230fbe93cbb7d7a962729190e780e7fe6403c7d0e4fbf6913ffb",
    "wal/seg_001.bin": "dc76b76d7ac787290275247cefd7a13dd974b5a1276cf25d36edf84fffc100c0",
    "wal/seg_002.bin": "35f498d4249caa7501e030052bd680188c044aca76b6807f7074ce4a6cf8ed52",
    "wal/seg_003.bin": "61eaee010e4473ae3ae37a79eceb5049debcb0924d7fb1edff47cc33a109f82e",
    "wal/seg_004.bin": "44694bb9bb98912fa6a5c15540a08969a9a384a21ef38e9b0913c5812c390b26",
    "wal/seg_005.bin": "e33e8c28100490c9953e72325cb1463253f9f6944e33e93b664edffaa1e7d5b3",
}


def _verify_pins() -> None:
    on_disk = {
        str(p.relative_to(DATA)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in DATA.rglob("*")
        if p.is_file()
    }
    assert on_disk == INPUT_PINS, "input fixtures under /app/data were modified"


# ---------------------------------------------------------------- mini-oracle


def _parse_wal_segment(path: Path) -> list[tuple]:
    blob = path.read_bytes()
    assert blob[:4] == b"WLOG" and blob[4] == 1, f"bad WAL header in {path.name}"
    off, n = 5, len(blob)
    records = []
    while off + 9 <= n:
        seq = int.from_bytes(blob[off : off + 8], "little")
        op = blob[off + 8]
        off += 9
        if op == 2:
            records.append((seq, "chk", None, None, None, None))
            continue
        if off + 1 > n:
            break
        ns_len = blob[off]
        off += 1
        if off + ns_len + 2 > n:
            break
        ns = blob[off : off + ns_len].decode()
        off += ns_len
        key_len = int.from_bytes(blob[off : off + 2], "little")
        off += 2
        if off + key_len > n:
            break
        key = blob[off : off + key_len].decode()
        off += key_len
        if op == 0:
            if off + 16 > n:
                break
            val = int.from_bytes(blob[off : off + 8], "little", signed=True)
            ts = int.from_bytes(blob[off + 8 : off + 16], "little")
            off += 16
            records.append((seq, "put", ns, key, val, ts))
        else:
            records.append((seq, "del", ns, key, None, None))
    return records


def _wal_ops() -> dict[int, tuple]:
    ops: dict[int, tuple] = {}
    for seg in sorted((DATA / "wal").glob("seg_*.bin")):
        for rec in _parse_wal_segment(seg):
            ops[rec[0]] = rec
    return ops


def _manifest_entries() -> list[dict]:
    entries = []
    for tier in ("tier_a.jsonl", "tier_b.jsonl", "tier_c.jsonl"):
        for line in (DATA / "manifests" / tier).read_text().splitlines():
            if line.strip():
                entries.append(json.loads(line))
    return entries


def _stripe_path(ns: str, sid: int) -> Path:
    if sid == 99:
        return DATA / "columns" / f"{ns}_merged.col"
    return DATA / "columns" / f"{ns}_{sid:03d}.col"


def _resolve(entries: list[dict], ns: str, gen: int) -> dict | None:
    candidates = [e for e in entries if e["ns"] == ns and e["gen"] <= gen]
    return max(candidates, key=lambda e: e["gen"]) if candidates else None


def _entry_verifies(entry: dict) -> bool:
    for sid in entry["stripes"]:
        path = _stripe_path(entry["ns"], sid)
        if not path.is_file():
            return False
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"][str(sid)]:
            return False
    return True


def _expected() -> dict:
    entries = _manifest_entries()
    namespaces = sorted({e["ns"] for e in entries})
    gens = sorted({e["gen"] for e in entries})

    restored = None
    for gen in gens:
        entry_by_ns = {ns: _resolve(entries, ns, gen) for ns in namespaces}
        if all(e is not None and _entry_verifies(e) for e in entry_by_ns.values()):
            restored = gen
    assert restored is not None, "fixtures must expose a consistent generation"

    ops = _wal_ops()
    checkpoint = max(seq for seq, rec in ops.items() if rec[1] == "chk")
    durable = {seq: rec for seq, rec in ops.items() if rec[1] != "chk" and seq <= checkpoint}
    rewound = {seq: rec for seq, rec in ops.items() if rec[1] != "chk" and seq > checkpoint}

    out = {
        "restored_generation": restored,
        "checkpoint_seq": checkpoint,
        "durable_ops": len(durable),
        "rewound_ops": len(rewound),
        "namespaces": {},
        "durable": durable,
        "rewound": rewound,
    }
    for ns in namespaces:
        entry = _resolve(entries, ns, restored)
        state: dict[str, tuple[int, int]] = {}
        for sid in entry["stripes"]:
            payload = json.loads(_stripe_path(ns, sid).read_text())
            for rec in payload["records"]:
                state[rec["k"]] = (rec["v"], rec["t"])
        held = set(state)
        for seq in sorted(durable):
            rec = durable[seq]
            if rec[2] != ns:
                continue
            if rec[1] == "put":
                state[rec[3]] = (rec[4], rec[5])
                held.add(rec[3])
            else:
                state.pop(rec[3], None)
        body = "".join(f"{k}\t{state[k][0]}\t{state[k][1]}\n" for k in sorted(state))
        out["namespaces"][ns] = {
            "entry": entry,
            "state": state,
            "removed": held - set(state),
            "body": body,
            "digest": hashlib.sha256(body.encode()).hexdigest(),
        }
    return out


def _report() -> dict:
    assert REPORT.is_file(), "missing /output/rewind-report.json"
    return json.loads(REPORT.read_text())


def _view_rows(ns: str) -> list[tuple[str, int, int]]:
    path = VIEW_DIR / f"{ns}.tsv"
    assert path.is_file(), f"missing view file for {ns}"
    rows = []
    for line in path.read_text().splitlines():
        parts = line.split("\t")
        assert len(parts) == 3, f"malformed view line: {line!r}"
        rows.append((parts[0], int(parts[1]), int(parts[2])))
    return rows


# ---------------------------------------------------------------- tests


def test_inputs_untouched_and_outputs_present():
    """Fixtures under /app/data stay byte-identical and the recovery artifacts exist."""
    _verify_pins()
    assert REPORT.is_file()
    for ns in ("events", "metrics"):
        assert (VIEW_DIR / f"{ns}.tsv").is_file()


def test_report_schema():
    """Report exposes the documented structure with integer counters and hex digests."""
    _verify_pins()
    report = _report()
    assert isinstance(report["restored_generation"], int)
    assert isinstance(report["checkpoint_seq"], int)
    assert isinstance(report["wal"]["durable_ops"], int)
    assert isinstance(report["wal"]["rewound_ops"], int)
    for ns in ("events", "metrics"):
        block = report["namespaces"][ns]
        for field in ("visible_stripes", "live_keys", "removed_keys", "value_total"):
            assert isinstance(block[field], int), f"{ns}.{field} must be an integer"
        digest = block["view_digest"]
        assert isinstance(digest, str) and len(digest) == 64
        int(digest, 16)


def test_restored_generation_is_newest_consistent():
    """The rewind anchors at the newest generation verifiable for every namespace."""
    _verify_pins()
    expected = _expected()
    report = _report()
    assert report["restored_generation"] == expected["restored_generation"]


def test_checkpoint_sequence():
    """checkpoint_seq is the newest checkpoint marker across all WAL segments."""
    _verify_pins()
    expected = _expected()
    assert _report()["checkpoint_seq"] == expected["checkpoint_seq"]


def test_wal_operation_accounting():
    """Durable/rewound counts reflect deduplicated, complete put/delete records only."""
    _verify_pins()
    expected = _expected()
    report = _report()
    assert report["wal"]["durable_ops"] == expected["durable_ops"]
    assert report["wal"]["rewound_ops"] == expected["rewound_ops"]


def test_events_view_rows():
    """The events view holds exactly the recomputed live rows in key order."""
    _verify_pins()
    expected = _expected()["namespaces"]["events"]
    rows = _view_rows("events")
    want = [(k, v, t) for k, (v, t) in sorted(expected["state"].items())]
    assert rows == want


def test_metrics_view_rows():
    """The metrics view holds exactly the recomputed live rows in key order."""
    _verify_pins()
    expected = _expected()["namespaces"]["metrics"]
    rows = _view_rows("metrics")
    want = [(k, v, t) for k, (v, t) in sorted(expected["state"].items())]
    assert rows == want


def test_view_files_canonical_bytes():
    """View files are byte-exact canonical TSV (sorted, tab-separated, LF, no header)."""
    _verify_pins()
    expected = _expected()
    for ns in ("events", "metrics"):
        got = (VIEW_DIR / f"{ns}.tsv").read_bytes()
        assert got == expected["namespaces"][ns]["body"].encode()


def test_view_digests_bind_report_to_files():
    """Reported digests hash the exact view file bytes and match the recomputed view."""
    _verify_pins()
    expected = _expected()
    report = _report()
    for ns in ("events", "metrics"):
        file_digest = hashlib.sha256((VIEW_DIR / f"{ns}.tsv").read_bytes()).hexdigest()
        assert report["namespaces"][ns]["view_digest"] == file_digest
        assert report["namespaces"][ns]["view_digest"] == expected["namespaces"][ns]["digest"]


def test_namespace_counters():
    """visible_stripes, live_keys, and removed_keys match the recomputed reconstruction."""
    _verify_pins()
    expected = _expected()
    report = _report()
    for ns in ("events", "metrics"):
        block = report["namespaces"][ns]
        exp = expected["namespaces"][ns]
        assert block["visible_stripes"] == len(exp["entry"]["stripes"])
        assert block["live_keys"] == len(exp["state"])
        assert block["removed_keys"] == len(exp["removed"])


def test_value_totals():
    """Per-namespace value_total equals the sum over the recomputed live rows."""
    _verify_pins()
    expected = _expected()
    report = _report()
    for ns in ("events", "metrics"):
        want = sum(v for v, _ in expected["namespaces"][ns]["state"].values())
        assert report["namespaces"][ns]["value_total"] == want


def test_unacknowledged_tail_left_out():
    """Operations past the newest checkpoint leave no trace in the views."""
    _verify_pins()
    expected = _expected()
    for ns in ("events", "metrics"):
        rows = {k: (v, t) for k, v, t in _view_rows(ns)}
        state = expected["namespaces"][ns]["state"]
        for rec in expected["rewound"].values():
            if rec[2] != ns:
                continue
            key = rec[3]
            if rec[1] == "put" and key not in state:
                assert key not in rows, f"unacknowledged put for {key} surfaced"
            if rec[1] == "del" and key in state:
                assert key in rows, f"unacknowledged delete removed {key}"
                assert rows[key] == state[key]


def test_dropped_and_orphan_stripes_excluded():
    """Keys from stripes outside the restored manifest entry never reach the views."""
    _verify_pins()
    expected = _expected()
    entries = _manifest_entries()
    for ns in ("events", "metrics"):
        visible = set(expected["namespaces"][ns]["entry"]["stripes"])
        durable_put_keys = {
            rec[3] for rec in expected["durable"].values() if rec[1] == "put" and rec[2] == ns
        }
        view_keys = {k for k, _, _ in _view_rows(ns)}
        all_sids = {
            sid for e in entries if e["ns"] == ns for sid in e["stripes"] if sid != 99
        }
        for sid in sorted(all_sids - visible):
            path = _stripe_path(ns, sid)
            if not path.is_file():
                continue
            for rec in json.loads(path.read_text())["records"]:
                key = rec["k"]
                if key in durable_put_keys or key in expected["namespaces"][ns]["state"]:
                    continue
                assert key not in view_keys, f"{key} leaked from non-visible stripe {sid}"


def test_stale_caches_not_echoed():
    """Sidecar digests and the boot snapshot's generation are not copied into the report."""
    _verify_pins()
    report = _report()
    boot = json.loads((DATA / "state" / "last_boot.json").read_text())
    assert report["restored_generation"] != boot["active_gen"]
    for ns in ("events", "metrics"):
        sidecar = json.loads((DATA / "sidecars" / f"{ns}.idx").read_text())
        assert report["namespaces"][ns]["view_digest"] != sidecar["digest"]
