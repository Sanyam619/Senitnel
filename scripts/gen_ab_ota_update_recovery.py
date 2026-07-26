#!/usr/bin/env python3
"""One-shot generator for tasks/ab-ota-update-recovery (authoring tool, not shipped)."""

from __future__ import annotations

import hashlib
import json
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks" / "ab-ota-update-recovery"
TASK_ROOT = "/opt/abdev"
ORACLE = Path(__file__).resolve().parent / "ab_ota_oracle_c"

SECTOR = 4096
TOTAL_SECTORS = 64
IMAGE_BYTES = SECTOR * TOTAL_SECTORS
PAYLOAD_SECTORS = 16
TREE_NODES = 15

AB_SLOT_A_MAGIC = b"SLTA"
AB_SLOT_B_MAGIC = b"SLTB"
AB_BOOT_MAGIC = b"ABLD"
AB_LAYOUT_VERSION = 1
AB_GUARD_WORD = 0xA5A5A5A5
AB_NO_PENDING = 0xFF

AB_PHASE_EMPTY = 0
AB_PHASE_LIVE = 1
AB_PHASE_STAGING = 2
AB_PHASE_RETIRED = 3

AB_SWAP_IDLE = 0
AB_SWAP_ARMED = 1
AB_SWAP_COMMIT = 2

AB_HDR_A0_SEC = 0
AB_HDR_A1_SEC = 1
AB_HDR_B0_SEC = 2
AB_HDR_B1_SEC = 3
AB_BL0_SEC = 4
AB_BL1_SEC = 5
AB_PAYLOAD_A_SEC = 6
AB_PAYLOAD_B_SEC = 22
AB_TREE_A_SEC = 38
AB_TREE_B_SEC = 42

SCENARIOS = ("case_alpha", "case_beta", "case_gamma", "case_delta")


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def wbin(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def pack_hdr(
    *,
    slot: int,
    phase: int,
    boot_ok: int,
    boot_count: int,
    generation: int,
    payload_bytes: int,
    root_hash: bytes,
) -> bytes:
    magic = AB_SLOT_A_MAGIC if slot == 0 else AB_SLOT_B_MAGIC
    body = bytearray(128)
    struct.pack_into(
        "<4sIIBB2xQI",
        body,
        0,
        magic,
        AB_LAYOUT_VERSION,
        boot_count,
        boot_ok,
        phase,
        generation,
        payload_bytes,
    )
    body[28:60] = root_hash[:32]
    struct.pack_into("<I", body, 60, crc32(bytes(body[:60])))
    return bytes(body)


def pack_bl(
    *,
    live_idx: int,
    pending_idx: int,
    swap_phase: int,
    commit_gen: int,
) -> bytes:
    body = bytearray(128)
    struct.pack_into(
        "<4sIBBBB",
        body,
        0,
        AB_BOOT_MAGIC,
        AB_LAYOUT_VERSION,
        live_idx,
        pending_idx,
        swap_phase,
        0,
    )
    struct.pack_into("<QI", body, 12, commit_gen, AB_GUARD_WORD)
    struct.pack_into("<I", body, 24, crc32(bytes(body[:24])))
    return bytes(body)


def empty_image() -> bytearray:
    return bytearray(IMAGE_BYTES)


def write_sector(img: bytearray, sec: int, data: bytes) -> None:
    chunk = data[:SECTOR].ljust(SECTOR, b"\x00")
    img[sec * SECTOR : (sec + 1) * SECTOR] = chunk


def payload_sectors(img: bytearray, slot: int) -> list[bytes]:
    base = AB_PAYLOAD_A_SEC if slot == 0 else AB_PAYLOAD_B_SEC
    return [bytes(img[(base + i) * SECTOR : (base + i + 1) * SECTOR]) for i in range(PAYLOAD_SECTORS)]


def build_tree_store(sectors: list[bytes]) -> tuple[bytes, bytes]:
    leaves = [sha256(sec) for sec in sectors]
    stored: list[bytes] = []
    level = leaves
    while len(level) > 1:
        nxt: list[bytes] = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else level[i]
            h = sha256(left + right)
            nxt.append(h)
            stored.append(h)
        level = nxt
    root = level[0]
    blob = b"".join(stored).ljust(TREE_NODES * 32, b"\x00")
    return root, blob


def write_slot(
    img: bytearray,
    slot: int,
    *,
    phase: int,
    boot_ok: int,
    boot_count: int,
    generation: int,
    payload_text: str,
) -> bytes:
    base = AB_PAYLOAD_A_SEC if slot == 0 else AB_PAYLOAD_B_SEC
    tree_sec = AB_TREE_A_SEC if slot == 0 else AB_TREE_B_SEC
    raw = payload_text.encode("utf-8")
    payload_bytes = len(raw)
    padded = raw.ljust(PAYLOAD_SECTORS * SECTOR, b"\x00")
    sectors = [padded[i * SECTOR : (i + 1) * SECTOR] for i in range(PAYLOAD_SECTORS)]
    for i, sec in enumerate(sectors):
        write_sector(img, base + i, sec)
    root, tree_blob = build_tree_store(sectors)
    write_sector(img, tree_sec, tree_blob)
    hdr = pack_hdr(
        slot=slot,
        phase=phase,
        boot_ok=boot_ok,
        boot_count=boot_count,
        generation=generation,
        payload_bytes=payload_bytes,
        root_hash=root,
    )
    m0 = AB_HDR_A0_SEC if slot == 0 else AB_HDR_B0_SEC
    m1 = AB_HDR_A1_SEC if slot == 0 else AB_HDR_B1_SEC
    write_sector(img, m0, hdr)
    write_sector(img, m1, hdr)
    return root


def write_boot(img: bytearray, **kwargs) -> None:
    bl = pack_bl(**kwargs)
    write_sector(img, AB_BL0_SEC, bl)
    write_sector(img, AB_BL1_SEC, bl)


def read_hdr(img: bytes | bytearray, sec: int) -> dict:
    raw = bytes(img[sec * SECTOR : sec * SECTOR + 128])
    boot_count, boot_ok, phase = struct.unpack_from("<IBB", raw, 8)
    generation, payload_bytes = struct.unpack_from("<QI", raw, 16)
    root_hash = raw[28:60]
    crc_stored = struct.unpack_from("<I", raw, 60)[0]
    return {
        "magic": raw[0:4],
        "boot_count": boot_count,
        "boot_ok": boot_ok,
        "phase": phase,
        "generation": generation,
        "payload_bytes": payload_bytes,
        "root_hash": root_hash,
        "crc_ok": crc32(raw[:60]) == crc_stored,
    }


def verify_chain(img: bytes | bytearray, slot: int, root_hash: bytes) -> bool:
    sectors = payload_sectors(bytearray(img), slot)
    leaves = [sha256(s) for s in sectors]
    tree_base = (AB_TREE_A_SEC if slot == 0 else AB_TREE_B_SEC) * SECTOR
    stored = img[tree_base : tree_base + TREE_NODES * 32]
    level = leaves
    idx = 0
    while len(level) > 1:
        nxt: list[bytes] = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else level[i]
            h = sha256(left + right)
            if idx < TREE_NODES and stored[idx * 32 : (idx + 1) * 32] != h:
                return False
            idx += 1
            nxt.append(h)
        level = nxt
    return level[0] == root_hash


def pick_hdr(img: bytes | bytearray, slot: int) -> dict | None:
    m0 = AB_HDR_A0_SEC if slot == 0 else AB_HDR_B0_SEC
    m1 = AB_HDR_A1_SEC if slot == 0 else AB_HDR_B1_SEC
    h0, h1 = read_hdr(img, m0), read_hdr(img, m1)
    ok0, ok1 = h0["crc_ok"], h1["crc_ok"]
    if not ok0 and not ok1:
        return None
    if ok0 and not ok1:
        return h0
    if ok1 and not ok0:
        return h1
    return h0 if h0["generation"] >= h1["generation"] else h1


def slot_view(img: bytes | bytearray, slot: int) -> dict:
    hdr = pick_hdr(img, slot)
    if not hdr:
        return {"phase": AB_PHASE_EMPTY, "boot_ok": 0, "verity_ok": False, "generation": 0}
    verity_ok = verify_chain(img, slot, hdr["root_hash"])
    return {
        "phase": hdr["phase"],
        "boot_ok": hdr["boot_ok"],
        "boot_count": hdr["boot_count"],
        "generation": hdr["generation"],
        "verity_ok": verity_ok,
    }


def recover(img: bytes | bytearray) -> tuple[bytearray, dict]:
    work = bytearray(img)
    va, vb = slot_view(img, 0), slot_view(img, 1)
    bl_raw = bytes(work[AB_BL0_SEC * SECTOR : AB_BL0_SEC * SECTOR + 128])
    live, pending, swap_phase, _pad = struct.unpack_from("<BBBB", bl_raw, 8)
    commit_gen = struct.unpack_from("<Q", bl_raw, 12)[0]

    a_live = va["phase"] == AB_PHASE_LIVE and va["verity_ok"]
    b_live = vb["phase"] == AB_PHASE_LIVE and vb["verity_ok"]
    a_ok = va["verity_ok"] and va["phase"] != AB_PHASE_RETIRED
    b_ok = vb["verity_ok"] and vb["phase"] != AB_PHASE_RETIRED

    act = "hold"
    if pending == 1 and vb["phase"] == AB_PHASE_STAGING and not vb["verity_ok"]:
        act = "rollback"
        live = 0 if a_live or a_ok else live
        vb["phase"] = AB_PHASE_RETIRED
        pending = AB_NO_PENDING
    elif live == 1 and not vb["verity_ok"] and a_live:
        act = "repoint"
        live = 0
        vb["phase"] = AB_PHASE_RETIRED
        pending = AB_NO_PENDING
    elif pending == 0 and va["phase"] == AB_PHASE_STAGING and va["verity_ok"] and not b_ok:
        act = "commit"
        va["phase"] = AB_PHASE_LIVE
        va["boot_ok"] = 1
        vb["phase"] = AB_PHASE_RETIRED
        live = 0
        pending = AB_NO_PENDING
    elif pending == 1 and not vb["verity_ok"] and a_live:
        act = "rollback"
        vb["phase"] = AB_PHASE_RETIRED
        pending = AB_NO_PENDING
        live = 0

    ha = pick_hdr(work, 0) or {}
    hb = pick_hdr(work, 1) or {}
    for slot, view, hdr in ((0, va, ha), (1, vb, hb)):
        if not hdr:
            continue
        packed = pack_hdr(
            slot=slot,
            phase=view["phase"],
            boot_ok=view.get("boot_ok", hdr.get("boot_ok", 0)),
            boot_count=view.get("boot_count", hdr.get("boot_count", 0)),
            generation=view.get("generation", hdr.get("generation", 0)),
            payload_bytes=hdr["payload_bytes"] if "payload_bytes" in hdr else 0,
            root_hash=hdr["root_hash"],
        )
        m0 = AB_HDR_A0_SEC if slot == 0 else AB_HDR_B0_SEC
        m1 = AB_HDR_A1_SEC if slot == 0 else AB_HDR_B1_SEC
        write_sector(work, m0, packed)
        write_sector(work, m1, packed)

    out_bl = pack_bl(
        live_idx=live,
        pending_idx=pending,
        swap_phase=AB_SWAP_IDLE,
        commit_gen=commit_gen + 1,
    )
    write_sector(work, AB_BL0_SEC, out_bl)
    write_sector(work, AB_BL1_SEC, out_bl)

    ba = 1 if va["phase"] == AB_PHASE_LIVE and va["verity_ok"] else 0
    bb = 1 if vb["phase"] == AB_PHASE_LIVE and vb["verity_ok"] else 0
    meta = {
        "live_slot": "a" if live == 0 else "b",
        "action": act,
        "bootable_slots": [x for x, on in (("a", ba), ("b", bb)) if on],
        "bootloader_hex": out_bl.hex(),
    }
    return work, meta


def scenario_case_alpha() -> tuple[bytearray, dict]:
    img = empty_image()
    write_slot(img, 0, phase=AB_PHASE_LIVE, boot_ok=1, boot_count=4, generation=10, payload_text="release-a-stable")
    write_slot(img, 1, phase=AB_PHASE_STAGING, boot_ok=0, boot_count=0, generation=11, payload_text="release-b-candidate")
    write_boot(img, live_idx=0, pending_idx=1, swap_phase=AB_SWAP_ARMED, commit_gen=40)
    corrupt = bytearray(img)
    # tear mirror B1 header
    off = AB_HDR_B1_SEC * SECTOR
    corrupt[off + 20 : off + 28] = b"\xff" * 8
    # partial payload/tree on B
    base = AB_PAYLOAD_B_SEC * SECTOR
    corrupt[base : base + 8 * SECTOR] = b"\x00" * (8 * SECTOR)
    tree_off = AB_TREE_B_SEC * SECTOR
    corrupt[tree_off : tree_off + 4 * 32] = b"\x00" * (4 * 32)
    golden = recover(bytes(corrupt))[1]
    return corrupt, golden


def scenario_case_beta() -> tuple[bytearray, dict]:
    img = empty_image()
    write_slot(img, 0, phase=AB_PHASE_LIVE, boot_ok=1, boot_count=6, generation=8, payload_text="known-good-a")
    write_slot(img, 1, phase=AB_PHASE_LIVE, boot_ok=1, boot_count=1, generation=9, payload_text="broken-b-image")
    write_boot(img, live_idx=1, pending_idx=AB_NO_PENDING, swap_phase=AB_SWAP_IDLE, commit_gen=12)
    corrupt = bytearray(img)
    base = AB_PAYLOAD_B_SEC * SECTOR
    corrupt[base : base + SECTOR] = b"corruption!" + b"\x00" * (SECTOR - 11)
    golden = recover(bytes(corrupt))[1]
    return corrupt, golden


def scenario_case_gamma() -> tuple[bytearray, dict]:
    img = empty_image()
    write_slot(img, 0, phase=AB_PHASE_LIVE, boot_ok=1, boot_count=3, generation=12, payload_text="gamma-a-live")
    write_slot(img, 1, phase=AB_PHASE_STAGING, boot_ok=0, boot_count=0, generation=13, payload_text="gamma-b-half")
    write_boot(img, live_idx=0, pending_idx=1, swap_phase=AB_SWAP_ARMED, commit_gen=20)
    corrupt = bytearray(img)
    off = AB_HDR_A1_SEC * SECTOR
    corrupt[off + 8 : off + 16] = b"\xde\xad\xbe\xef" * 2
    base = AB_PAYLOAD_B_SEC * SECTOR
    corrupt[base + 4 * SECTOR : base + 8 * SECTOR] = b"\x55" * (4 * SECTOR)
    golden = recover(bytes(corrupt))[1]
    return corrupt, golden


def scenario_case_delta() -> tuple[bytearray, dict]:
    img = empty_image()
    write_slot(img, 0, phase=AB_PHASE_STAGING, boot_ok=0, boot_count=0, generation=15, payload_text="delta-a-ready")
    write_slot(img, 1, phase=AB_PHASE_STAGING, boot_ok=0, boot_count=0, generation=16, payload_text="delta-b-bad")
    write_boot(img, live_idx=1, pending_idx=0, swap_phase=AB_SWAP_COMMIT, commit_gen=30)
    corrupt = bytearray(img)
    base = AB_PAYLOAD_B_SEC * SECTOR
    corrupt[base : base + 2 * SECTOR] = b"\x00" * (2 * SECTOR)
    golden = recover(bytes(corrupt))[1]
    return corrupt, golden


BUILDERS = {
    "case_alpha": scenario_case_alpha,
    "case_beta": scenario_case_beta,
    "case_gamma": scenario_case_gamma,
    "case_delta": scenario_case_delta,
}


def emit_tests(template: str) -> str:
    return template


def emit_solve_sh() -> str:
    return f"""#!/bin/bash
set -euo pipefail

mkdir -p /output
cd {TASK_ROOT}

cat > config/active_policy.toml <<'EOF'
# Rollout wave 3 policy table
rule_order=rollback_staging_b,repoint_live_b_fail,commit_staging_a,rollback_live_b_fail,hold
allow_commit=true
mirror_pick=generation
finalize_commit_gen=bump
verify_payload_chain=true
write_both_metadata_mirrors=true
write_both_control_mirrors=true
default_action=hold
retire_on_integrity_fail=true
clear_pending_on_rollback=true
promote_staging_boot_ok=1
swap_phase_idle=0
report_bootloader_mirror=0
scenario_batch=all
field_override=enabled
integrity_gate=strict
EOF

cat > config/recover.env <<'EOF'
# Environment consumed by ops/reconcile_field.sh
AB_POLICY_FILE={TASK_ROOT}/config/active_policy.toml
AB_DATA_ROOT={TASK_ROOT}/data/scenarios
AB_OUT_ROOT=/output
AB_REPORT=/output/recovery.json
AB_VERIFY_BOOTSIM=1
AB_PRESERVE_INPUTS=1
EOF

ops/reconcile_field.sh

for case in case_alpha case_beta case_gamma case_delta; do
  bin/bootsim "/output/fixed_${{case}}.img" >/dev/null
done
"""


def main() -> None:
    test_template_path = TASK / "tests" / "test_outputs.py"
    if not test_template_path.is_file():
        raise SystemExit("tests/test_outputs.py template missing before regeneration")
    test_template = test_template_path.read_text()

    if TASK.exists():
        import shutil

        shutil.rmtree(TASK)

    w(
        TASK / "task.toml",
        """version = "2.0"

[metadata]
author_name = "anonymous"
author_email = "anonymous"
difficulty = "hard"
category = "system-administration"
subcategories = []
number_of_milestones = 0
codebase_size = "small"
languages = ["bash"]
tags = ["embedded", "firmware", "ota", "a-b-slots", "integrity", "recovery"]
expert_time_estimate_min = 120
junior_time_estimate_min = 360

[agent]
timeout_sec = 1800

[verifier]
timeout_sec = 900

[environment]
allow_internet = false
build_timeout_sec = 900
cpus = 2
memory_mb = 4096
storage_mb = 10240
""",
    )

    w(
        TASK / "instruction.md",
        f"""Field units copied four raw flash images into `{TASK_ROOT}/data/scenarios/` after mains dropped during over-the-air delivery. Symptoms vary by unit: sometimes the device boots an older userspace build, sometimes the controller refuses handoff citing integrity failure, and the redundant metadata copies at the front of each image disagree about which generation is current.

The on-disk layout is documented under `{TASK_ROOT}/docs/flash_layout.md`. Canonical recovery precedence and finalize semantics are documented under `{TASK_ROOT}/docs/recovery_policy.md`. The fleet rollout driver reads `{TASK_ROOT}/config/active_policy.toml` and `{TASK_ROOT}/config/recover.env` (which selects the policy file path), then invokes the prebuilt `{TASK_ROOT}/bin/recover` through `{TASK_ROOT}/ops/reconcile_field.sh`. Read-only diagnostics are `{TASK_ROOT}/bin/slotstat` (boot-attempt counters only) and `{TASK_ROOT}/bin/bootsim` (integrity check on a candidate image). The report schema is in `{TASK_ROOT}/include/ab_report.h`.

Align the live rollout configuration with the canonical policy, run the field reconcile driver, and produce outputs for every bundled scenario under `{TASK_ROOT}/data/scenarios/`: `/output/recovery.json` with `live_slot`, `action`, `bootable_slots`, and `bootloader_hex` per case, plus `/output/fixed_<basename>.img` for each input (`/output/fixed_case_alpha.img`, `/output/fixed_case_beta.img`, `/output/fixed_case_gamma.img`, `/output/fixed_case_delta.img`). Corrected images must stay the same byte length as their inputs, preserve payload and digest-chain sectors, and leave at least one integrity-clean live copy. Do not modify scenario images under `{TASK_ROOT}/data/scenarios/` or rebuild shipped recovery binaries.
""",
    )

    w(
        TASK / "output_contract.toml",
        """user_visible_outputs = [
  "/output/recovery.json",
  "/output/fixed_case_alpha.img",
  "/output/fixed_case_beta.img",
  "/output/fixed_case_gamma.img",
  "/output/fixed_case_delta.img",
]

internal_harness_files = [
  "/tests/test_outputs.py",
]

[structured_outputs.recovery]
target = "/output/recovery.json"
format = "json"
instruction_checks = [
  "scenarios",
  "live_slot",
  "action",
  "bootable_slots",
  "bootloader_hex",
]
""",
    )

    w(
        TASK / "environment" / "include" / "ab_layout.h",
        f"""#ifndef AB_LAYOUT_H
#define AB_LAYOUT_H

#include <stddef.h>
#include <stdint.h>

#define AB_SECTOR_SIZE {SECTOR}
#define AB_TOTAL_SECTORS {TOTAL_SECTORS}
#define AB_IMAGE_BYTES (AB_SECTOR_SIZE * AB_TOTAL_SECTORS)
#define AB_PAYLOAD_SECTORS {PAYLOAD_SECTORS}
#define AB_TREE_NODES {TREE_NODES}

#define AB_SLOT_A_MAGIC "SLTA"
#define AB_SLOT_B_MAGIC "SLTB"
#define AB_BOOT_MAGIC "ABLD"
#define AB_LAYOUT_VERSION 1
#define AB_GUARD_WORD 0xA5A5A5A5U
#define AB_NO_PENDING 0xFFU

#define AB_PHASE_EMPTY 0
#define AB_PHASE_LIVE 1
#define AB_PHASE_STAGING 2
#define AB_PHASE_RETIRED 3

#define AB_SWAP_IDLE 0
#define AB_SWAP_ARMED 1
#define AB_SWAP_COMMIT 2

#define AB_HDR_A0_SEC {AB_HDR_A0_SEC}
#define AB_HDR_A1_SEC {AB_HDR_A1_SEC}
#define AB_HDR_B0_SEC {AB_HDR_B0_SEC}
#define AB_HDR_B1_SEC {AB_HDR_B1_SEC}
#define AB_BL0_SEC {AB_BL0_SEC}
#define AB_BL1_SEC {AB_BL1_SEC}
#define AB_PAYLOAD_A_SEC {AB_PAYLOAD_A_SEC}
#define AB_PAYLOAD_B_SEC {AB_PAYLOAD_B_SEC}
#define AB_TREE_A_SEC {AB_TREE_A_SEC}
#define AB_TREE_B_SEC {AB_TREE_B_SEC}

#pragma pack(push, 1)
typedef struct {{
    char magic[4];
    uint32_t version;
    uint32_t boot_count;
    uint8_t boot_ok;
    uint8_t phase;
    uint8_t pad0[2];
    uint64_t generation;
    uint32_t payload_bytes;
    uint8_t root_hash[32];
    uint32_t hdr_crc32;
    uint8_t pad1[64];
}} slot_hdr_t;

typedef struct {{
    char magic[4];
    uint32_t version;
    uint8_t live_idx;
    uint8_t pending_idx;
    uint8_t swap_phase;
    uint8_t pad0;
    uint64_t commit_gen;
    uint32_t guard;
    uint32_t bl_crc32;
    uint8_t pad1[100];
}} boot_ldr_t;
#pragma pack(pop)

#endif
""",
    )

    w(
        TASK / "environment" / "include" / "ab_report.h",
        """#ifndef AB_REPORT_H
#define AB_REPORT_H

/* Recovery tool output: /output/recovery.json
 * Top-level object contains key "scenarios" mapping each case basename to:
 *   live_slot    - "a" or "b" for the reconciled boot index
 *   action       - one of AB_ACT_HOLD, AB_ACT_ROLLBACK, AB_ACT_REPOINT, AB_ACT_COMMIT
 *   bootable_slots - JSON array of slot ids that are live-phase and integrity-clean
 *   bootloader_hex - lowercase hex of the 128-byte first control-sector mirror
 *
 * Each case also writes /output/fixed_<basename>.img (full AB_IMAGE_BYTES).
 */

#define AB_ACT_HOLD "hold"
#define AB_ACT_ROLLBACK "rollback"
#define AB_ACT_REPOINT "repoint"
#define AB_ACT_COMMIT "commit"

#endif
""",
    )

    w(
        TASK / "environment" / "include" / "ab_api.h",
        """#ifndef AB_API_H
#define AB_API_H

#include <stddef.h>
#include <stdint.h>

typedef struct ab_image ab_image;

ab_image *p4_open_image(const char *path);
void p4_close_image(ab_image *img);
int q1_walk_digest(const uint8_t *img, int slot_idx, int *ok);
int r7_probe_chain(const ab_image *img, int slot_idx, char *out, size_t cap);
int step_a_read_counters(const ab_image *img, int slot_idx, uint32_t *boot_count, uint8_t *boot_ok);

#endif
""",
    )

    w(
        TASK / "environment" / "docs" / "flash_layout.md",
        f"""# Flash image layout

Images are a fixed {SECTOR}-byte sector array ({TOTAL_SECTORS} sectors). Sectors {AB_HDR_A0_SEC} and {AB_HDR_A1_SEC} are redundant metadata mirrors for copy A; sectors {AB_HDR_B0_SEC} and {AB_HDR_B1_SEC} mirror copy B. Each metadata sector begins with a 128-byte `slot_hdr_t`. Sectors {AB_BL0_SEC} and {AB_BL1_SEC} duplicate a 128-byte `boot_ldr_t` control record.

Copy A payload occupies sectors {AB_PAYLOAD_A_SEC}–{AB_PAYLOAD_A_SEC + PAYLOAD_SECTORS - 1}; copy B payload occupies sectors {AB_PAYLOAD_B_SEC}–{AB_PAYLOAD_B_SEC + PAYLOAD_SECTORS - 1}. Each payload sector is 4096 bytes. Digest chains for each copy begin at sector {AB_TREE_A_SEC} (copy A) and {AB_TREE_B_SEC} (copy B): interior nodes are 32-byte SHA-256 values stored sequentially ({TREE_NODES} nodes for sixteen payload sectors). The metadata `root_hash` must equal the final rolling digest.

Phase bytes: 0 empty, 1 live, 2 staging, 3 retired. Unclean power loss may leave redundant metadata torn, digest nodes partially updated, or the control record pointing at an integrity-failing copy.
""",
    )

    w(
        TASK / "environment" / "docs" / "recovery_policy.md",
        f"""# Firmware recovery policy

Fleet recovery is driven by `{TASK_ROOT}/config/active_policy.toml` and executed through `{TASK_ROOT}/bin/recover` (via `{TASK_ROOT}/ops/reconcile_field.sh`). The policy file controls rule precedence and whether staging commits are permitted.

## Policy file keys

- `rule_order` — comma-separated rule names evaluated top to bottom; the first matching rule wins.
- `allow_commit` — when `true`, the commit rule may promote a verified staging copy; when `false`, commit is skipped.

Rule names:

| Name | Action when matched |
|------|---------------------|
| `rollback_staging_b` | `rollback` when pending copy B is staging and fails integrity |
| `repoint_live_b_fail` | `repoint` when live copy B fails integrity but copy A is live |
| `commit_staging_a` | `commit` when pending copy A is verified staging and copy B is not integrity-clean |
| `rollback_live_b_fail` | `rollback` when pending copy B fails integrity and copy A is live |
| `hold` | `hold` — default finalize with mirror reconciliation only |

Canonical precedence: `rollback_staging_b,repoint_live_b_fail,commit_staging_a,rollback_live_b_fail,hold` with `allow_commit=true`.

## Rollout environment (`recover.env`)

`{TASK_ROOT}/ops/reconcile_field.sh` sources `{TASK_ROOT}/config/recover.env` before invoking recover. Keys:

- `AB_POLICY_FILE` — path to the active policy TOML passed to `recover --policy`.
- `AB_DATA_ROOT` — directory containing read-only scenario images.
- `AB_OUT_ROOT` — directory for corrected images (`fixed_<case>.img`).
- `AB_REPORT` — path for the JSON recovery report.
- `AB_VERIFY_BOOTSIM` — when set to `1`, post-reconcile bootsim checks are expected in field runbooks.
- `AB_PRESERVE_INPUTS` — when set to `1`, scenario images under `AB_DATA_ROOT` must not be modified.

## Mirror selection

For each copy (A or B), read both redundant `slot_hdr_t` mirrors. A mirror is usable when its header CRC32 validates. If only one mirror validates, use it. If both validate, keep the one with the higher `generation` field.

Read both `boot_ldr_t` control-sector mirrors (sectors {AB_BL0_SEC} and {AB_BL1_SEC}). Use the first mirror whose CRC32 validates and whose `guard` equals `AB_GUARD_WORD`. Treat `pending_idx == AB_NO_PENDING` (0xFF) as no pending copy.

## Slot integrity view

For each copy, after picking metadata:

- Walk the existing digest-chain sectors (do not rewrite them) and verify they match the picked header's `root_hash`.
- `verity_ok` is true only when that walk succeeds.
- `a_live` / `b_live`: phase is live and `verity_ok`.
- `a_ok` / `b_ok`: `verity_ok` and phase is not retired.

Payload sectors and digest-chain sectors are preserved byte-for-byte from the input image. Recovery only reconciles metadata mirrors and the control-sector pair.

## Finalize writes

1. Copy the full input image into the work buffer.
2. Apply any phase changes from the matched action to the in-memory slot views.
3. For each copy, pack a fresh `slot_hdr_t` using the reconciled phase and `boot_ok`, but reuse `boot_count`, `generation`, `payload_bytes`, and `root_hash` from the picked input header. Recompute `hdr_crc32`. Write the same packed header to both metadata mirrors for that copy.
4. Pack a fresh `boot_ldr_t` with reconciled `live_idx` and `pending_idx` (or `AB_NO_PENDING`), `swap_phase = AB_SWAP_IDLE`, `guard = AB_GUARD_WORD`, and `commit_gen` equal to the picked input control record's `commit_gen` plus one. Recompute `bl_crc32`. Write identical bytes to both control-sector mirrors.
5. Set bootable flags when the reconciled copy is live-phase with passing integrity.

The report's `bootloader_hex` is the lowercase hex of the first control-sector mirror (sector {AB_BL0_SEC}) after finalize.
""",
    )

    w(
        TASK / "environment" / "lib" / "ab_internal.h",
        """#pragma once
#include <stdio.h>
#include <stdint.h>

typedef struct ab_image {
    FILE *fp;
    uint8_t *map;
    size_t len;
} ab_image;
""",
    )

    w(
        TASK / "environment" / "lib" / "p4_open.c",
        """#include "ab_api.h"
#include "ab_layout.h"

#include <stdlib.h>
#include <string.h>

#include "ab_internal.h"

ab_image *p4_open_image(const char *path) {
    ab_image *img = calloc(1, sizeof(*img));
    if (!img) return NULL;
    img->fp = fopen(path, "rb");
    if (!img->fp) { free(img); return NULL; }
    fseek(img->fp, 0, SEEK_END);
    long sz = ftell(img->fp);
    fseek(img->fp, 0, SEEK_SET);
    if (sz != AB_IMAGE_BYTES) { fclose(img->fp); free(img); return NULL; }
    img->len = (size_t)sz;
    img->map = malloc(img->len);
    if (!img->map) { fclose(img->fp); free(img); return NULL; }
    if (fread(img->map, 1, img->len, img->fp) != img->len) {
        fclose(img->fp); free(img->map); free(img); return NULL;
    }
    return img;
}

void p4_close_image(ab_image *img) {
    if (!img) return;
    if (img->fp) fclose(img->fp);
    free(img->map);
    free(img);
}
""",
    )

    w(
        TASK / "environment" / "lib" / "q1_walk.c",
        """#include "ab_api.h"
#include "ab_layout.h"

#include <openssl/evp.h>
#include <string.h>

static void digest(const uint8_t *data, size_t len, uint8_t out[32]) {
    unsigned char buf[EVP_MAX_MD_SIZE];
    unsigned int dlen = 0;
    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    EVP_DigestInit_ex(ctx, EVP_sha256(), NULL);
    EVP_DigestUpdate(ctx, data, len);
    EVP_DigestFinal_ex(ctx, buf, &dlen);
    EVP_MD_CTX_free(ctx);
    memcpy(out, buf, 32);
}

int q1_walk_digest(const uint8_t *img, int slot_idx, int *ok) {
    if (!img || !ok) return -1;
    size_t base = (size_t)(slot_idx == 0 ? AB_PAYLOAD_A_SEC : AB_PAYLOAD_B_SEC) * AB_SECTOR_SIZE;
    size_t tree_base = (size_t)(slot_idx == 0 ? AB_TREE_A_SEC : AB_TREE_B_SEC) * AB_SECTOR_SIZE;
    uint8_t leaves[AB_PAYLOAD_SECTORS][32];
    for (int i = 0; i < AB_PAYLOAD_SECTORS; i++) {
        digest(img + base + (size_t)i * AB_SECTOR_SIZE, AB_SECTOR_SIZE, leaves[i]);
    }
    const uint8_t *stored = img + tree_base;
  int idx = 0;
    uint8_t level[AB_PAYLOAD_SECTORS][32];
    int count = AB_PAYLOAD_SECTORS;
    memcpy(level, leaves, sizeof(leaves));
    while (count > 1) {
        int next = 0;
        for (int i = 0; i < count; i += 2) {
            uint8_t pair[64];
            memcpy(pair, level[i], 32);
            if (i + 1 < count) memcpy(pair + 32, level[i + 1], 32);
            else memcpy(pair + 32, level[i], 32);
            digest(pair, 64, level[next]);
            if (idx < AB_TREE_NODES && memcmp(level[next], stored + (size_t)idx * 32, 32) != 0) {
                *ok = 0;
                return 0;
            }
            idx++;
            next++;
        }
        count = next;
    }
    size_t hdr_sec = (size_t)(slot_idx == 0 ? AB_HDR_A0_SEC : AB_HDR_B0_SEC);
    const slot_hdr_t *hdr = (const slot_hdr_t *)(img + hdr_sec * AB_SECTOR_SIZE);
    *ok = memcmp(level[0], hdr->root_hash, 32) == 0;
    return 0;
}
""",
    )

    w(
        TASK / "environment" / "lib" / "r7_probe.c",
        """#include "ab_api.h"
#include "ab_layout.h"

#include <stdio.h>

#include "ab_internal.h"

int r7_probe_chain(const ab_image *img, int slot_idx, char *out, size_t cap) {
    if (!img || !out || cap < 16) return -1;
    int ok = 0;
    if (q1_walk_digest(img->map, slot_idx, &ok)) return -1;
    snprintf(out, cap, "slot=%c integrity=%s", slot_idx == 0 ? 'a' : 'b', ok ? "pass" : "fail");
    return 0;
}
""",
    )

    w(
        TASK / "environment" / "lib" / "step_a_counters.c",
        """#include "ab_api.h"
#include "ab_layout.h"

#include <stddef.h>
#include <string.h>
#include <zlib.h>

#include "ab_internal.h"

static int hdr_ok(const slot_hdr_t *hdr) {
    uint32_t got = (uint32_t)crc32(0, (const unsigned char *)hdr, offsetof(slot_hdr_t, hdr_crc32));
    return got == hdr->hdr_crc32;
}

int step_a_read_counters(const ab_image *img, int slot_idx, uint32_t *boot_count, uint8_t *boot_ok) {
    if (!img || !boot_count || !boot_ok) return -1;
    size_t s0 = (size_t)(slot_idx == 0 ? AB_HDR_A0_SEC : AB_HDR_B0_SEC) * AB_SECTOR_SIZE;
    size_t s1 = (size_t)(slot_idx == 0 ? AB_HDR_A1_SEC : AB_HDR_B1_SEC) * AB_SECTOR_SIZE;
    const slot_hdr_t *h0 = (const slot_hdr_t *)(img->map + s0);
    const slot_hdr_t *h1 = (const slot_hdr_t *)(img->map + s1);
    const slot_hdr_t *pick = NULL;
    if (hdr_ok(h0) && !hdr_ok(h1)) pick = h0;
    else if (!hdr_ok(h0) && hdr_ok(h1)) pick = h1;
    else if (hdr_ok(h0) && hdr_ok(h1)) pick = h0->generation >= h1->generation ? h0 : h1;
  else return -1;
    *boot_count = pick->boot_count;
    *boot_ok = pick->boot_ok;
    return 0;
}
""",
    )

    w(
        TASK / "environment" / "lib" / "m3_apply.c",
        (ORACLE / "m3_apply.c").read_text(),
    )

    w(
        TASK / "environment" / "lib" / "ab_policy.c",
        (ORACLE / "ab_policy.c").read_text(),
    )

    w(
        TASK / "environment" / "include" / "ab_policy.h",
        (ORACLE / "ab_policy.h").read_text(),
    )

    w(
        TASK / "environment" / "tools" / "slotstat.c",
        """#include "ab_api.h"

#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: slotstat <image>\\n");
        return 2;
    }
    ab_image *img = p4_open_image(argv[1]);
    if (!img) { perror("open"); return 1; }
    for (int slot = 0; slot < 2; slot++) {
        uint32_t boot_count = 0;
        uint8_t boot_ok = 0;
        if (step_a_read_counters(img, slot, &boot_count, &boot_ok)) {
            printf("slot=%c boot_count=invalid boot_ok=invalid\\n", slot == 0 ? 'a' : 'b');
            continue;
        }
        printf("slot=%c boot_count=%u boot_ok=%u\\n", slot == 0 ? 'a' : 'b', boot_count, boot_ok);
    }
    p4_close_image(img);
    return 0;
}
""",
    )

    w(
        TASK / "environment" / "tools" / "bootsim.c",
        """#include "ab_api.h"
#include "ab_layout.h"

#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>

#include "ab_internal.h"

static int bl_ok(const boot_ldr_t *bl) {
    uint32_t got = (uint32_t)crc32(0, (const unsigned char *)bl, offsetof(boot_ldr_t, bl_crc32));
    return got == bl->bl_crc32 && bl->guard == AB_GUARD_WORD;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: bootsim <image>\\n");
        return 2;
    }
    ab_image *img = p4_open_image(argv[1]);
    if (!img) { perror("open"); return 1; }
    const boot_ldr_t *b0 = (const boot_ldr_t *)(img->map + AB_BL0_SEC * AB_SECTOR_SIZE);
    const boot_ldr_t *b1 = (const boot_ldr_t *)(img->map + AB_BL1_SEC * AB_SECTOR_SIZE);
    const boot_ldr_t *bl = bl_ok(b0) ? b0 : (bl_ok(b1) ? b1 : NULL);
    if (!bl) { fprintf(stderr, "control record invalid\\n"); p4_close_image(img); return 1; }
    int ok = 0;
    if (q1_walk_digest(img->map, (int)bl->live_idx, &ok) || !ok) {
        fprintf(stderr, "integrity failure on live copy\\n");
        p4_close_image(img);
        return 1;
    }
    printf("live=%c verity=pass\\n", bl->live_idx == 0 ? 'a' : 'b');
    p4_close_image(img);
    return 0;
}
""",
    )

    w(
        TASK / "environment" / "tools" / "recover.c",
        (ORACLE / "recover.c").read_text(),
    )

    w(
        TASK / "environment" / "Makefile",
        f"""CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -I{TASK_ROOT}/include -I{TASK_ROOT}/lib
LDFLAGS = -lz -lcrypto -lssl

LIB_SRCS = lib/p4_open.c lib/q1_walk.c lib/r7_probe.c lib/step_a_counters.c
LIB_OBJS = $(LIB_SRCS:.c=.o)
TOOLS = bin/slotstat bin/bootsim bin/recover

.PHONY: all clean

all: $(TOOLS) lib/libab.a

lib/libab.a: $(LIB_OBJS)
\tmkdir -p lib
\tar rcs $@ $(LIB_OBJS)

bin:
\tmkdir -p bin

bin/slotstat: bin lib/libab.a tools/slotstat.c
\t$(CC) $(CFLAGS) -o $@ tools/slotstat.c lib/libab.a $(LDFLAGS)

bin/bootsim: bin lib/libab.a tools/bootsim.c
\t$(CC) $(CFLAGS) -o $@ tools/bootsim.c lib/libab.a $(LDFLAGS)

bin/recover: bin lib/libab.a tools/recover.c lib/m3_apply.o lib/ab_policy.o
\t$(CC) $(CFLAGS) -o $@ tools/recover.c lib/m3_apply.o lib/ab_policy.o lib/libab.a $(LDFLAGS)

lib/m3_apply.o: lib/m3_apply.c
\t$(CC) $(CFLAGS) -c -o $@ lib/m3_apply.c

lib/ab_policy.o: lib/ab_policy.c
\t$(CC) $(CFLAGS) -c -o $@ lib/ab_policy.c

%.o: %.c
\t$(CC) $(CFLAGS) -c -o $@ $<

clean:
\trm -f lib/*.o tools/*.o bin/* lib/libab.a
""",
    )

    w(
        TASK / "environment" / "Dockerfile",
        f"""# syntax=docker/dockerfile:1

# Canonical GCC toolchain image (C/C++ tasks; agents compile in-container).
FROM public.ecr.aws/docker/library/gcc:13-bookworm@sha256:930f2ebe239275fa67226654cb79273ea34eee672ae61c8a39f689c37fb7ac5c

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Agent session stack (tmux, asciinema) plus verifier and build deps in one apt transaction.
RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        asciinema=2.2.0-1 \\
        bash \\
        ca-certificates \\
        coreutils \\
        libssl-dev \\
        procps \\
        python3 \\
        python3-pip \\
        tmux=3.3a-3 \\
        zlib1g-dev \\
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color

RUN tmux -V \\
    && asciinema --version \\
    && tmux new-session -d -s _smoke \\
    && tmux has-session -t _smoke \\
    && tmux kill-session -t _smoke

RUN pip3 install --no-cache-dir --break-system-packages \\
    pytest==8.4.1 \\
    pytest-json-ctrf==0.3.5

COPY include {TASK_ROOT}/include
COPY lib {TASK_ROOT}/lib
COPY tools {TASK_ROOT}/tools
COPY docs {TASK_ROOT}/docs
COPY data {TASK_ROOT}/data
COPY config {TASK_ROOT}/config
COPY Makefile {TASK_ROOT}/Makefile
COPY ops {TASK_ROOT}/ops
COPY packaging {TASK_ROOT}/packaging

RUN make -C {TASK_ROOT} clean all \\
    && chmod 755 {TASK_ROOT}/ops/check_image.sh {TASK_ROOT}/ops/reconcile_field.sh

RUN tmux -V \\
    && asciinema --version \\
    && tmux new-session -d -s _smoke \\
    && tmux has-session -t _smoke \\
    && tmux kill-session -t _smoke

WORKDIR {TASK_ROOT}
ENV PATH="{TASK_ROOT}/bin:${{PATH}}"
""",
    )

    w(
        TASK / "environment" / ".dockerignore",
        """.git
.gitignore
**/__pycache__/
**/*.pyc
**/.pytest_cache/
**/.mypy_cache/
**/.ruff_cache/
**/node_modules/
**/target/
**/dist/
**/build/
**/.venv/
**/venv/
.env
*.log
*.o
*.a
bin/
lib/*.o
tools/*.o
solution/
tests/
""",
    )

    extras = {
        "environment/config/build_flags.mk": "WARNINGS = -Wall -Wextra -Wpedantic\nSTD = -std=c11\n",
        "environment/config/paths.mk": f"PREFIX = {TASK_ROOT}\nBINDIR = $(PREFIX)/bin\n",
        "environment/config/active_policy.toml": (
            "# Rollout wave 3 policy table\n"
            "rule_order=hold,rollback_live_b_fail,rollback_staging_b,repoint_live_b_fail,commit_staging_a\n"
            "allow_commit=false\n"
            "mirror_pick=legacy_crc_only\n"
            "finalize_commit_gen=hold\n"
            "verify_payload_chain=false\n"
            "write_both_metadata_mirrors=false\n"
            "write_both_control_mirrors=false\n"
            "default_action=hold\n"
            "retire_on_integrity_fail=false\n"
            "clear_pending_on_rollback=false\n"
            "promote_staging_boot_ok=0\n"
            "swap_phase_idle=0\n"
            "report_bootloader_mirror=0\n"
            "scenario_batch=none\n"
            "field_override=disabled\n"
            "integrity_gate=relaxed\n"
        ),
        "environment/config/recover.env": (
            f"# Environment consumed by ops/reconcile_field.sh\n"
            f"AB_POLICY_FILE={TASK_ROOT}/config/staging_policy.toml\n"
            f"AB_DATA_ROOT={TASK_ROOT}/data/scenarios\n"
            f"AB_OUT_ROOT=/output\n"
            f"AB_REPORT=/output/recovery.json\n"
            f"AB_VERIFY_BOOTSIM=0\n"
            f"AB_PRESERVE_INPUTS=1\n"
        ),
        "environment/config/staging_policy.toml": (
            "# Staging overlay copy for lab benches\n"
            "rule_order=hold,rollback_live_b_fail,rollback_staging_b,repoint_live_b_fail,commit_staging_a\n"
            "allow_commit=false\n"
            "mirror_pick=legacy_crc_only\n"
            "finalize_commit_gen=hold\n"
            "verify_payload_chain=false\n"
            "write_both_metadata_mirrors=false\n"
            "write_both_control_mirrors=false\n"
            "default_action=hold\n"
            "retire_on_integrity_fail=false\n"
            "clear_pending_on_rollback=false\n"
            "promote_staging_boot_ok=0\n"
            "swap_phase_idle=0\n"
            "report_bootloader_mirror=0\n"
            "scenario_batch=none\n"
        ),
        "environment/data/README.txt": "Scenario images are read-only crash copies. Bundled cases: case_alpha, case_beta, case_gamma, case_delta.\n",
        "environment/docs/glossary.txt": "Digest chain terms mirror flash_layout.md.\n",
        "environment/ops/check_image.sh": f"#!/bin/sh\n{TASK_ROOT}/bin/slotstat \"$1\"\n",
        "environment/ops/reconcile_field.sh": f"""#!/bin/bash
set -euo pipefail
mkdir -p /output
set -a
if [ -f {TASK_ROOT}/config/recover.env ]; then
  # shellcheck disable=SC1091
  . {TASK_ROOT}/config/recover.env
fi
set +a
POLICY="${{AB_POLICY_FILE:-{TASK_ROOT}/config/active_policy.toml}}"
DATA="${{AB_DATA_ROOT:-{TASK_ROOT}/data/scenarios}}"
OUT="${{AB_OUT_ROOT:-/output}}"
REPORT="${{AB_REPORT:-/output/recovery.json}}"
exec {TASK_ROOT}/bin/recover \\
  --policy "$POLICY" \\
  --data "$DATA" \\
  --out "$OUT" \\
  --report "$REPORT"
""",
        "environment/ops/field_notes.txt": "Images are flat sector arrays. slotstat reports counters only; use bootsim after recovery.\n",
        "environment/packaging/version.txt": "abdev-tools 1.0.0\n",
        "environment/tools/README.txt": "recover reads config/active_policy.toml; slotstat and bootsim are read-only diagnostics.\n",
    }
    for rel, text in extras.items():
        w(TASK / rel, text)

    for name, fn in BUILDERS.items():
        img, _ = fn()
        wbin(TASK / "environment" / "data" / "scenarios" / f"{name}.img", bytes(img))

    w(TASK / "tests" / "test.sh", """#!/bin/bash

# Verifier dependencies are installed in environment/Dockerfile.

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
""")

    w(TASK / "tests" / "test_outputs.py", emit_tests(test_template))
    w(TASK / "solution" / "solve.sh", emit_solve_sh())

    print(f"Wrote task to {TASK}")


if __name__ == "__main__":
    main()
