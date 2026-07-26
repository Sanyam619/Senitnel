import json
import subprocess
from pathlib import Path

SCENARIOS = ["case_alpha", "case_beta", "case_gamma", "case_delta"]
ACTIONS = ("hold", "rollback", "repoint", "commit")
SECTOR = 4096
IMAGE_BYTES = 262144
PAYLOAD_SECTORS = 16
TREE_NODES = 15
AB_PHASE_LIVE = 1
AB_PHASE_STAGING = 2
AB_PHASE_RETIRED = 3
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
DATA = Path("/opt/abdev/data/scenarios")
OUT = Path("/output")


def _crc32(data: bytes) -> int:
    poly = 0xEDB88320
    state = 0xFFFFFFFF
    for byte in data:
        state ^= byte
        for _ in range(8):
            state = (state >> 1) ^ poly if state & 1 else state >> 1
    return (~state) & 0xFFFFFFFF


def _sha256(data: bytes) -> bytes:
    proc = subprocess.run(
        ["sha256sum"],
        input=data,
        capture_output=True,
        check=True,
        text=False,
    )
    return bytes.fromhex(proc.stdout.decode().split()[0])


def _payload_sectors(img: bytes, slot: int) -> list[bytes]:
    base = AB_PAYLOAD_A_SEC if slot == 0 else AB_PAYLOAD_B_SEC
    return [img[(base + i) * SECTOR : (base + i + 1) * SECTOR] for i in range(PAYLOAD_SECTORS)]


def _read_hdr(img: bytes, sec: int):
    raw = img[sec * SECTOR : sec * SECTOR + 128]
    boot_count = int.from_bytes(raw[8:12], "little")
    boot_ok = raw[12]
    phase = raw[13]
    generation = int.from_bytes(raw[16:24], "little")
    payload_bytes = int.from_bytes(raw[24:28], "little")
    root_hash = raw[28:60]
    crc_ok = _crc32(raw[:60]) == int.from_bytes(raw[60:64], "little")
    return boot_count, boot_ok, phase, generation, payload_bytes, root_hash, crc_ok


def _verify_chain(img: bytes, slot: int, root_hash: bytes) -> bool:
    sectors = _payload_sectors(img, slot)
    leaves = [_sha256(s) for s in sectors]
    tree_base = (AB_TREE_A_SEC if slot == 0 else AB_TREE_B_SEC) * SECTOR
    stored = img[tree_base : tree_base + TREE_NODES * 32]
    level = leaves
    idx = 0
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else level[i]
            h = _sha256(left + right)
            if idx < TREE_NODES and stored[idx * 32 : (idx + 1) * 32] != h:
                return False
            idx += 1
            nxt.append(h)
        level = nxt
    return level[0] == root_hash


def _pick_hdr(img: bytes, slot: int):
    m0 = AB_HDR_A0_SEC if slot == 0 else AB_HDR_B0_SEC
    m1 = AB_HDR_A1_SEC if slot == 0 else AB_HDR_B1_SEC
    h0 = _read_hdr(img, m0)
    h1 = _read_hdr(img, m1)
    if not h0[6] and not h1[6]:
        return None
    if h0[6] and not h1[6]:
        return h0
    if h1[6] and not h0[6]:
        return h1
    return h0 if h0[3] >= h1[3] else h1


def _slot_view(img: bytes, slot: int):
    hdr = _pick_hdr(img, slot)
    if not hdr:
        return 0, 0, False
    return hdr[2], hdr[1], _verify_chain(img, slot, hdr[5])


def _recover(img: bytes) -> tuple[bytes, dict]:
    work = bytearray(img)
    va = list(_slot_view(img, 0))
    vb = list(_slot_view(img, 1))
    bl_raw = bytes(work[AB_BL0_SEC * SECTOR : AB_BL0_SEC * SECTOR + 128])
    live = bl_raw[8]
    pending = bl_raw[9]
    commit_gen = int.from_bytes(bl_raw[12:20], "little")
    a_live = va[0] == AB_PHASE_LIVE and va[2]
    a_ok = va[2] and va[0] != AB_PHASE_RETIRED
    b_ok = vb[2] and vb[0] != AB_PHASE_RETIRED
    act = "hold"
    if pending == 1 and vb[0] == AB_PHASE_STAGING and not vb[2]:
        act = "rollback"
        live = 0 if a_live or a_ok else live
        vb[0] = AB_PHASE_RETIRED
        pending = 0xFF
    elif live == 1 and not vb[2] and a_live:
        act = "repoint"
        live = 0
        vb[0] = AB_PHASE_RETIRED
        pending = 0xFF
    elif pending == 0 and va[0] == AB_PHASE_STAGING and va[2] and not b_ok:
        act = "commit"
        va[0] = AB_PHASE_LIVE
        va[1] = 1
        vb[0] = AB_PHASE_RETIRED
        live = 0
        pending = 0xFF
    elif pending == 1 and not vb[2] and a_live:
        act = "rollback"
        vb[0] = AB_PHASE_RETIRED
        pending = 0xFF
        live = 0
    for slot, view in ((0, va), (1, vb)):
        hdr = _pick_hdr(work, slot)
        if not hdr:
            continue
        body = bytearray(128)
        magic = b"SLTA" if slot == 0 else b"SLTB"
        body[0:4] = magic
        body[4:8] = (1).to_bytes(4, "little")
        body[8:12] = int(hdr[0]).to_bytes(4, "little")
        body[12] = view[1] if len(view) > 1 else hdr[1]
        body[13] = view[0]
        body[16:24] = int(hdr[3]).to_bytes(8, "little")
        body[24:28] = int(hdr[4]).to_bytes(4, "little")
        body[28:60] = hdr[5]
        body[60:64] = _crc32(bytes(body[:60])).to_bytes(4, "little")
        m0 = AB_HDR_A0_SEC if slot == 0 else AB_HDR_B0_SEC
        m1 = AB_HDR_A1_SEC if slot == 0 else AB_HDR_B1_SEC
        work[m0 * SECTOR : m0 * SECTOR + 128] = body
        work[m1 * SECTOR : m1 * SECTOR + 128] = body
    out_bl = bytearray(128)
    out_bl[0:4] = b"ABLD"
    out_bl[4:8] = (1).to_bytes(4, "little")
    out_bl[8] = live
    out_bl[9] = pending
    out_bl[12:20] = (commit_gen + 1).to_bytes(8, "little")
    out_bl[20:24] = (0xA5A5A5A5).to_bytes(4, "little")
    out_bl[24:28] = _crc32(bytes(out_bl[:24])).to_bytes(4, "little")
    work[AB_BL0_SEC * SECTOR : AB_BL0_SEC * SECTOR + 128] = out_bl
    work[AB_BL1_SEC * SECTOR : AB_BL1_SEC * SECTOR + 128] = out_bl
    ba = va[0] == AB_PHASE_LIVE and va[2]
    bb = vb[0] == AB_PHASE_LIVE and vb[2]
    meta = {
        "live_slot": "a" if live == 0 else "b",
        "action": act,
        "bootable_slots": [x for x, on in (("a", ba), ("b", bb)) if on],
        "bootloader_hex": bytes(out_bl).hex(),
    }
    return bytes(work), meta


def _scenario_meta(case: str) -> dict:
    _, meta = _recover((DATA / f"{case}.img").read_bytes())
    return meta


def _load_report() -> dict:
    path = OUT / "recovery.json"
    assert path.is_file(), "missing /output/recovery.json"
    return json.loads(path.read_text())


def test_recover_cli_preinstalled():
    """Fleet recovery driver is shipped as a prebuilt binary."""
    assert Path("/opt/abdev/bin/recover").is_file()


def test_report_lists_all_cases():
    """Recovery report names every bundled power-cut image."""
    report = _load_report()
    bundled = sorted(p.stem for p in DATA.glob("*.img"))
    assert set(bundled) == set(SCENARIOS)
    for name in bundled:
        assert name in report["scenarios"]


def test_fixed_images_exist():
    """Each scenario has a matching corrected raw image on disk."""
    for name in SCENARIOS:
        path = OUT / f"fixed_{name}.img"
        assert path.is_file(), f"missing fixed image for {name}"
        assert path.stat().st_size == IMAGE_BYTES


def test_fixed_images_match_input_size():
    """Corrected raw images keep the same byte length as their scenario inputs."""
    for name in SCENARIOS:
        inp = DATA / f"{name}.img"
        fixed = OUT / f"fixed_{name}.img"
        assert fixed.stat().st_size == inp.stat().st_size


def test_fixed_images_match_reconciled_layout():
    """Corrected images match the reconciled layout for every case."""
    for name in SCENARIOS:
        expected, _ = _recover((DATA / f"{name}.img").read_bytes())
        rebuilt = (OUT / f"fixed_{name}.img").read_bytes()
        assert rebuilt == expected


def test_recovery_fields_complete():
    """Every case reports live choice, action, bootable set, and bootloader bytes."""
    report = _load_report()
    for name in SCENARIOS:
        entry = report["scenarios"][name]
        assert entry["live_slot"] in ("a", "b")
        assert entry["action"] in ACTIONS
        assert isinstance(entry["bootable_slots"], list)
        assert isinstance(entry["bootloader_hex"], str) and entry["bootloader_hex"]


def test_case_alpha_interrupted_secondary():
    """Interrupted delivery on the secondary copy still leaves the primary bootable."""
    expected = _scenario_meta("case_alpha")
    entry = _load_report()["scenarios"]["case_alpha"]
    for key in ("live_slot", "action", "bootable_slots", "bootloader_hex"):
        assert entry[key] == expected[key]


def test_case_beta_integrity_failure_secondary():
    """Secondary payload integrity failure with a healthy primary copy."""
    expected = _scenario_meta("case_beta")
    entry = _load_report()["scenarios"]["case_beta"]
    for key in ("live_slot", "action", "bootable_slots", "bootloader_hex"):
        assert entry[key] == expected[key]


def test_case_gamma_mirror_disagreement():
    """Torn redundant metadata on the primary copy still leaves a bootable primary."""
    expected = _scenario_meta("case_gamma")
    entry = _load_report()["scenarios"]["case_gamma"]
    for key in ("live_slot", "action", "bootable_slots", "bootloader_hex"):
        assert entry[key] == expected[key]


def test_case_delta_mid_swap_crash():
    """Power loss during swap leaves verified staging work on the primary copy."""
    expected = _scenario_meta("case_delta")
    entry = _load_report()["scenarios"]["case_delta"]
    for key in ("live_slot", "action", "bootable_slots", "bootloader_hex"):
        assert entry[key] == expected[key]


def test_boot_simulator_accepts_fixed_images():
    """Deterministic boot simulator boots the reported live copy with passing integrity checks."""
    for name in SCENARIOS:
        proc = subprocess.run(
            ["/opt/abdev/bin/bootsim", str(OUT / f"fixed_{name}.img")],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stderr
        report = _load_report()["scenarios"][name]
        assert f"live={report['live_slot']}" in proc.stdout
        assert "verity=pass" in proc.stdout


def test_anti_brick_invariant():
    """Every corrected image leaves at least one integrity-clean live copy."""
    for name in SCENARIOS:
        img = (OUT / f"fixed_{name}.img").read_bytes()
        views = [_slot_view(img, 0), _slot_view(img, 1)]
        live_count = sum(1 for phase, _boot_ok, ok in views if phase == AB_PHASE_LIVE and ok)
        assert live_count >= 1


def test_slotstat_runs_on_inputs():
    """Bundled counter reader runs cleanly against each scenario image."""
    for name in SCENARIOS:
        proc = subprocess.run(
            ["/opt/abdev/bin/slotstat", str(DATA / f"{name}.img")],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stderr
        assert "boot_count" in proc.stdout


def test_bootloader_hex_matches_fixed_image():
    """Reported bootloader bytes match the first control-sector mirror on the fixed image."""
    report = _load_report()
    for name in SCENARIOS:
        img = (OUT / f"fixed_{name}.img").read_bytes()
        bl0 = img[AB_BL0_SEC * SECTOR : AB_BL0_SEC * SECTOR + 128].hex()
        assert report["scenarios"][name]["bootloader_hex"] == bl0
