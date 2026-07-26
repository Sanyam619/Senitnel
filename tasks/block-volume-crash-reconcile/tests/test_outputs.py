import json
import re
import subprocess
from pathlib import Path

SCENARIOS = ["shard_a", "shard_b", "shard_c", "shard_d", "shard_e", "shard_f", "shard_g", "shard_h", "shard_i", "shard_j"]

# Verifier-side integrity ledgers pin the crash images and the format-spec
# surface (docs, layout headers, inspector source). Living under /tests/ so
# an agent that tampers with /opt/kvfs/data or /opt/kvfs/docs cannot mask the
# drift by rewriting an agent-side manifest.
LEDGERS = Path("/tests/ledgers")
SCENARIOS_LEDGER = LEDGERS / "scenarios.sha256"
FORMAT_LEDGER = LEDGERS / "format.sha256"
KVFS_ROOT = Path("/opt/kvfs")

# Verifier-owned probe binary built by conftest.py against the agent's live
# libkvfs.a + m3_apply.o. Exercises reconcile_b_image() directly.
PROBE_BIN = Path("/tmp/kvfs-verify-probe")

# Recovery policy file the agent must arm with these exact literal tokens.
# Equivalent spellings ("true" for booleans, alternate value keywords, etc.)
# are rejected even when the runtime would honour the same semantics.
POLICY_INI = KVFS_ROOT / "config" / "recovery_policy.ini"
NORMATIVE_POLICY = {
    "order": "tx_id",
    "forget_mode": "invalidate_earlier",
    "metadata_used_end": "28",
    "patch_zero_pad": "1",
    "preserve_superblocks": "1",
    "prefer": "epoch",
}
BLOCK = 4096
TOTAL_BLOCKS = 256
INODE_TABLE_BLK = 2
INODE_CAPACITY = 128
INODE_SIZE = 128
DATA = Path("/opt/kvfs/data/scenarios")
OUT = Path("/output")


_B = 4096
_TB = 256
_IT = 2
_IC = 128
_IS = 128
_BM = 6
_BB = 2
_JB = 8
_JL = 20
_DS = 28
_MG = b"KVFS"
_T0, _T1, _T2, _T3, _T4 = 0, 161, 162, 163, 164


def _c(data: bytes) -> int:
    poly = 0xEDB88320
    state = 0xFFFFFFFF
    for byte in data:
        state ^= byte
        for _ in range(8):
            state = (state >> 1) ^ poly if state & 1 else state >> 1
    return (~state) & 0xFFFFFFFF


def _h(data: bytes) -> str:
    proc = subprocess.run(["sha256sum"], input=data, capture_output=True, check=True, text=False)
    return proc.stdout.decode().split()[0]


def _wb(img: bytearray, blk: int, data: bytes) -> None:
    chunk = data[:_B].ljust(_B, b"\x00")
    img[blk * _B : (blk + 1) * _B] = chunk


def _bm(used: set[int]) -> bytes:
    bits = bytearray(_BB * _B)
    for blk in used:
        if blk < _TB:
            bits[blk // 8] |= 1 << (blk % 8)
    return bytes(bits)


def _view(path: Path) -> tuple[bytearray, dict]:
    img = bytearray(path.read_bytes())

    def _rs(blk: int):
        raw = bytes(img[blk * _B : (blk + 1) * _B])
        return (
            raw[0:4],
            int.from_bytes(raw[48:56], "little"),
            int.from_bytes(raw[56:64], "little"),
            int.from_bytes(raw[64:68], "little"),
            int.from_bytes(raw[68:72], "little"),
        )

    cands = []
    for blk in (0, 1):
        magic, epoch, durable_tx, primary_ok, crc = _rs(blk)
        if magic != _MG:
            continue
        body = img[blk * _B : blk * _B + 68]
        if _c(body) != crc or primary_ok != 1:
            continue
        cands.append((epoch, durable_tx, blk))
    chosen = max(cands, key=lambda item: (item[0], item[1], -item[2]))[2]

    base = _JB * _B
    end = (_JB + _JL) * _B
    pos = base
    sealed: set[int] = set()
    patches: dict[int, list[tuple[int, bytes]]] = {}
    forgets: list[tuple[int, list[int]]] = []
    open_tx = None
    while pos < end:
        tag = img[pos]
        if tag in (_T0, 0):
            break
        length = int.from_bytes(img[pos + 1 : pos + 3], "little")
        body = bytes(img[pos + 3 : pos + 3 + length])
        pos += 3 + length
        if tag == _T1:
            open_tx = int.from_bytes(body[0:8], "little")
            patches.setdefault(open_tx, [])
        elif tag == _T2 and open_tx is not None:
            bn = int.from_bytes(body[0:4], "little")
            patches[open_tx].append((bn, body[4:]))
        elif tag == _T3:
            sealed.add(int.from_bytes(body[0:8], "little"))
            open_tx = None
        elif tag == _T4:
            tx = int.from_bytes(body[0:8], "little")
            n = int.from_bytes(body[8:10], "little")
            blocks = [int.from_bytes(body[10 + 4 * i : 14 + 4 * i], "little") for i in range(n)]
            forgets.append((tx, blocks))

    suppress: dict[int, int] = {}
    for tx, blocks in forgets:
        if tx not in sealed:
            continue
        for blk in blocks:
            suppress[blk] = max(suppress.get(blk, 0), tx)

    work = bytearray(img)
    for tx in sorted(sealed):
        for bn, payload in patches.get(tx, []):
            if bn in suppress and suppress[bn] > tx:
                continue
            _wb(work, bn, payload)

    files: dict[str, str] = {}
    used: set[int] = set(range(_DS))
    for iid in range(_IC):
        off = _IT * _B + iid * _IS
        raw = bytes(work[off : off + _IS])
        mode = int.from_bytes(raw[0:2], "little")
        size = int.from_bytes(raw[4:8], "little")
        if mode != 1:
            continue
        name = raw[12:60].split(b"\x00", 1)[0].decode("utf-8")
        direct = [int.from_bytes(raw[60 + 2 * i : 62 + 2 * i], "little") for i in range(12)]
        bl = [b for b in direct if b]
        used.update(bl)
        chunks = []
        remain = size
        for blk in bl:
            if remain <= 0:
                break
            chunks.append(bytes(work[blk * _B : blk * _B + min(_B, remain)]))
            remain -= _B
        content = b"".join(chunks)[:size]
        if name.startswith("/"):
            files[name] = _h(content)

    bitmap = _bm(used)
    work[_BM * _B : _BM * _B + len(bitmap)] = bitmap
    meta = {"chosen_superblock": chosen, "files": files, "bitmap_hex": bitmap.hex()}
    return work, meta


def _sha256_hex(data: bytes) -> str:
    proc = subprocess.run(
        ["sha256sum"],
        input=data,
        capture_output=True,
        check=True,
        text=False,
    )
    return proc.stdout.decode().split()[0]


def _reference_view(path: Path) -> dict:
    _, meta = _view(path)
    return meta


def _reconcile_work(path: Path) -> bytearray:
    work, _ = _view(path)
    return work


def _files_from_image_bytes(work: bytes | bytearray) -> dict[str, str]:
    files: dict[str, str] = {}
    for inode_id in range(INODE_CAPACITY):
        off = INODE_TABLE_BLK * BLOCK + inode_id * INODE_SIZE
        raw = bytes(work[off : off + INODE_SIZE])
        mode = int.from_bytes(raw[0:2], "little")
        size = int.from_bytes(raw[4:8], "little")
        if mode != 1:
            continue
        name = raw[12:60].split(b"\x00", 1)[0].decode("utf-8")
        direct = [int.from_bytes(raw[60 + 2 * i : 62 + 2 * i], "little") for i in range(12)]
        block_list = [b for b in direct if b]
        chunks = []
        remain = size
        for blk in block_list:
            if remain <= 0:
                break
            chunk = bytes(work[blk * BLOCK : blk * BLOCK + min(BLOCK, remain)])
            chunks.append(chunk)
            remain -= BLOCK
        content = b"".join(chunks)[:size]
        if name.startswith("/"):
            files[name] = _sha256_hex(content)
    return files


def _load_report() -> dict:
    path = OUT / "recovered_state.json"
    assert path.is_file(), "missing /output/recovered_state.json"
    return json.loads(path.read_text())


def _assert_ledger(ledger: Path, root: Path) -> None:
    assert ledger.is_file(), f"missing verifier ledger {ledger}"
    for line in ledger.read_text().splitlines():
        if not line.strip():
            continue
        want, rel = line.split(None, 1)
        target = root / rel
        assert target.is_file(), f"ledger references missing file {rel}"
        got = _sha256_hex(target.read_bytes())
        assert got == want, f"fixture drift under {root}: {rel}"


def _parse_policy_kv() -> dict[str, str]:
    """Return the {key: value} map from the policy INI.

    Lines are ``key = value`` or ``key=value`` (whitespace around "=" is
    tolerated). Values must be a single bare token; "true"/"false" and
    quoted strings are treated as-is so equivalent spellings can be
    rejected explicitly by the tests below.
    """
    assert POLICY_INI.is_file(), f"missing {POLICY_INI}"
    kv: dict[str, str] = {}
    for line in POLICY_INI.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith(";"):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            continue
        match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(\S+)\s*$", stripped)
        if not match:
            continue
        kv[match.group(1)] = match.group(2)
    return kv


def _run_probe(image: Path) -> dict[str, str]:
    assert PROBE_BIN.is_file() and image.is_file(), (PROBE_BIN, image)
    proc = subprocess.run(
        [str(PROBE_BIN), str(image)],
        capture_output=True,
        text=True,
        check=True,
    )
    out: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip()
    return out


def test_report_top_level():
    """Recovery report names every bundled scenario shard."""
    report = _load_report()
    assert "scenarios" in report
    for name in SCENARIOS:
        assert name in report["scenarios"], f"missing scenario {name}"


def test_report_matches_scenario_directory():
    """Recovery report lists exactly the scenario basenames shipped under the data directory."""
    report = _load_report()
    on_disk = sorted(p.stem for p in DATA.glob("*.img"))
    assert sorted(report["scenarios"].keys()) == on_disk


def _sha256_file(path: Path) -> str:
    proc = subprocess.run(
        ["sha256sum", str(path)],
        capture_output=True,
        check=True,
        text=True,
    )
    return proc.stdout.split()[0]


def test_scenario_inputs_unchanged():
    """Bundled scenario images under the read-only data directory are left unmodified."""
    manifest = json.loads((DATA.parent / "scenario_manifest.json").read_text())
    for name, digest in manifest.items():
        assert _sha256_file(DATA / f"{name}.img") == digest


def test_volpeek_binary_unchanged():
    """The bundled inspector binary is not rebuilt or replaced."""
    expected = Path("/opt/kvfs/packaging/volpeek.sha256").read_text().strip()
    assert _sha256_file(Path("/opt/kvfs/bin/volpeek")) == expected


def test_rebuilt_images_exist():
    """Each scenario has a matching rebuilt raw image on disk."""
    for name in SCENARIOS:
        path = OUT / f"rebuilt_{name}.img"
        assert path.is_file(), f"missing rebuilt image for {name}"
        assert path.stat().st_size == BLOCK * TOTAL_BLOCKS


def test_rebuilt_images_match_reconciled_layout():
    """Rebuilt raw images match the reconciled allocation map and patched block payloads."""
    for name in SCENARIOS:
        expected = _reconcile_work(DATA / f"{name}.img")
        rebuilt = (OUT / f"rebuilt_{name}.img").read_bytes()
        assert rebuilt == bytes(expected)


def test_all_scenarios_report_complete_fields():
    """Every shard reports header choice, reconciled file digests, and allocation map."""
    report = _load_report()
    for name in SCENARIOS:
        entry = report["scenarios"][name]
        assert entry["chosen_superblock"] in (0, 1)
        assert isinstance(entry["files"], dict)
        assert isinstance(entry["bitmap_hex"], str) and entry["bitmap_hex"]
        expected = _reference_view(DATA / f"{name}.img")
        assert entry["chosen_superblock"] == expected["chosen_superblock"]
        assert entry["bitmap_hex"] == expected["bitmap_hex"]
        assert entry["files"] == expected["files"]


def test_rebuilt_images_carry_report_file_payloads():
    """Rebuilt images expose the same live file payloads named in the recovery report."""
    report = _load_report()
    for name in SCENARIOS:
        files = _files_from_image_bytes((OUT / f"rebuilt_{name}.img").read_bytes())
        assert files == report["scenarios"][name]["files"]


def test_shard_a_file_digests():
    """Primary shard restores updated note content and stable config payload."""
    expected = _reference_view(DATA / "shard_a.img")
    report = _load_report()["scenarios"]["shard_a"]
    assert report["files"]["/notes.txt"] == expected["files"]["/notes.txt"]
    assert report["files"]["/config/app.cfg"] == expected["files"]["/config/app.cfg"]


def test_shard_b_forget_suppression():
    """Reuse shard keeps beta payload when an older patch targeted the same physical block."""
    expected = _reference_view(DATA / "shard_b.img")
    report = _load_report()["scenarios"]["shard_b"]
    assert "/alpha.dat" not in report["files"]
    assert report["files"]["/beta.dat"] == expected["files"]["/beta.dat"]


def test_shard_c_header_choice():
    """Disagreeing redundant headers resolve to the durable generation with later sealed work."""
    expected = _reference_view(DATA / "shard_c.img")
    report = _load_report()["scenarios"]["shard_c"]
    assert report["chosen_superblock"] == expected["chosen_superblock"]
    assert report["files"]["/ledger.tsv"] == expected["files"]["/ledger.tsv"]
    assert report["files"]["/audit.tsv"] == expected["files"]["/audit.tsv"]


def test_shard_d_bitmap_consistency():
    """Rebuilt free list matches inode-derived allocation after sealed work only."""
    expected = _reference_view(DATA / "shard_d.img")
    report = _load_report()["scenarios"]["shard_d"]
    assert report["bitmap_hex"] == expected["bitmap_hex"]
    assert report["files"]["/cache.bin"] == expected["files"]["/cache.bin"]


def test_shard_e_invalid_header_decoy():
    """A newer-looking redundant header with primary_ok cleared must not win selection."""
    expected = _reference_view(DATA / "shard_e.img")
    report = _load_report()["scenarios"]["shard_e"]
    assert report["chosen_superblock"] == expected["chosen_superblock"]
    assert report["bitmap_hex"] == expected["bitmap_hex"]
    assert report["files"]["/archive.zip"] == expected["files"]["/archive.zip"]


def test_shard_f_out_of_band_tx_order():
    """Sealed work from a higher tx_id logged after an earlier id still wins after reconciliation."""
    expected = _reference_view(DATA / "shard_f.img")
    report = _load_report()["scenarios"]["shard_f"]
    assert report["files"]["/order.dat"] == expected["files"]["/order.dat"]
    assert report["bitmap_hex"] == expected["bitmap_hex"]


def test_shard_g_unsealed_tx_ignored():
    """A crash-interrupted transaction must not overwrite durable sealed payload on the same block."""
    expected = _reference_view(DATA / "shard_g.img")
    report = _load_report()["scenarios"]["shard_g"]
    assert report["files"]["/hold.dat"] == expected["files"]["/hold.dat"]
    assert report["bitmap_hex"] == expected["bitmap_hex"]


def test_shard_h_intra_tx_patch_order():
    """When one sealed transaction patches the same data block twice, the later journal patch wins."""
    expected = _reference_view(DATA / "shard_h.img")
    report = _load_report()["scenarios"]["shard_h"]
    assert report["files"]["/layer.dat"] == expected["files"]["/layer.dat"]
    assert report["bitmap_hex"] == expected["bitmap_hex"]


def test_shard_i_durable_tx_lag():
    """Sealed redo beyond the chosen header durable_tx watermark must still land in the rebuilt image."""
    expected = _reference_view(DATA / "shard_i.img")
    report = _load_report()["scenarios"]["shard_i"]
    assert report["files"]["/lag.dat"] == expected["files"]["/lag.dat"]
    assert report["bitmap_hex"] == expected["bitmap_hex"]


def test_shard_j_unsealed_forget_ignored():
    """An unsealed BLK_FORGET must not erase a previously sealed payload on the same block."""
    expected = _reference_view(DATA / "shard_j.img")
    report = _load_report()["scenarios"]["shard_j"]
    assert report["files"]["/keep.dat"] == expected["files"]["/keep.dat"]
    assert report["bitmap_hex"] == expected["bitmap_hex"]


def test_volpeek_runs_on_scenario_inputs():
    """Bundled inspector runs cleanly against each scenario image."""
    for name in SCENARIOS:
        proc = subprocess.run(
            ["/opt/kvfs/bin/volpeek", str(DATA / f"{name}.img")],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stderr
        assert "chosen_superblock=" in proc.stdout


def test_shard_a_live_paths():
    """Primary shard recovery report lists every reconciled live path."""
    expected = _reference_view(DATA / "shard_a.img")
    report = _load_report()["scenarios"]["shard_a"]
    assert sorted(report["files"].keys()) == sorted(expected["files"].keys())


def test_cross_scenario_inode_counts():
    """Each scenario exposes the expected number of live paths after reconciliation."""
    report = _load_report()
    for name in SCENARIOS:
        expected = _reference_view(DATA / f"{name}.img")
        live = len(report["scenarios"][name]["files"])
        assert live == len(expected["files"])


def test_scenario_input_ledger_intact():
    """Crash images match the verifier-side scenario ledger under /tests/ledgers/."""
    _assert_ledger(SCENARIOS_LEDGER, DATA)


def test_format_surface_ledger_intact():
    """Format spec (headers, docs, inspector source) matches the verifier ledger."""
    _assert_ledger(FORMAT_LEDGER, KVFS_ROOT)


def test_policy_tokens_are_literal_and_exact():
    """recovery_policy.ini carries the normative literal tokens with exact values.

    Equivalent spellings that happen to parse the same way at runtime
    (``true``/``false`` for the boolean toggles, alternate replay-order
    keywords, generation-preference synonyms) are rejected. This mirrors the
    package-registry ``bound_mode = "half_open"`` literal check: the goal is
    to force the agent to arm the site-standard policy on purpose rather than
    stumble into a semantically equivalent configuration by accident.
    """
    parsed = _parse_policy_kv()
    for key, expected in NORMATIVE_POLICY.items():
        assert key in parsed, f"policy missing key {key}"
        assert parsed[key] == expected, (
            f"policy key {key} must be literally {expected!r}, got {parsed[key]!r}"
        )
    banned = {
        "order": {"journal", "tx-id", "ascending", "asc", "tx_id_asc"},
        "forget_mode": {"forward", "older", "invalidate", "earlier"},
        "prefer": {"durable_tx", "generation", "tx", "newest"},
        "patch_zero_pad": {"0", "true", "false", "yes", "no", "on", "off"},
        "preserve_superblocks": {"0", "true", "false", "yes", "no", "on", "off"},
    }
    for key, bad_values in banned.items():
        assert parsed.get(key) not in bad_values, (
            f"policy key {key} must not use rejected spelling {parsed.get(key)!r}"
        )


def test_probe_agrees_with_reference_on_every_scenario():
    """Verifier-owned probe (links libkvfs directly) matches the reference view."""
    for name in SCENARIOS:
        img_path = DATA / f"{name}.img"
        probe = _run_probe(img_path)
        expected_work = _reconcile_work(img_path)
        expected_digest = _sha256_hex(bytes(expected_work))
        expected_meta = _reference_view(img_path)
        assert probe["digest"] == expected_digest, name
        assert probe["bitmap"] == expected_meta["bitmap_hex"], name
        assert probe["chosen"] == str(expected_meta["chosen_superblock"]), name


def test_rebuilt_journal_region_preserved():
    """Rebuilt images keep the crash-copy journal region byte-identical.

    The reconciliation contract replays sealed redo into the data area and
    rebuilds the allocation map; the raw journal blocks 8..27 must remain
    the crash-copy bytes so a later forensic pass can audit the redo log.
    An agent that ``cleans'' the journal (writing zeros or a compacted log)
    to make later runs cheaper still trips this test.
    """
    journal_start = 8 * BLOCK
    journal_end = (8 + 20) * BLOCK
    for name in SCENARIOS:
        crash = (DATA / f"{name}.img").read_bytes()
        rebuilt = (OUT / f"rebuilt_{name}.img").read_bytes()
        assert (
            rebuilt[journal_start:journal_end]
            == crash[journal_start:journal_end]
        ), f"{name}: rebuilt image mutated journal region"


def test_rebuilt_superblocks_preserved():
    """Rebuilt images preserve both redundant superblocks byte-for-byte.

    The site policy mandates ``preserve_superblocks = 1`` — the reconciled
    view chooses one header for reads but writes back the crash bytes for
    both blocks so subsequent tools can still see the disagreement.
    """
    for name in SCENARIOS:
        crash = (DATA / f"{name}.img").read_bytes()
        rebuilt = (OUT / f"rebuilt_{name}.img").read_bytes()
        assert rebuilt[:2 * BLOCK] == crash[:2 * BLOCK], (
            f"{name}: rebuilt image overwrote the redundant superblocks"
        )
