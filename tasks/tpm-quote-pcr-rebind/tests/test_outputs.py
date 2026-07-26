"""Verifier tests for TPM quote PCR rebind outcomes."""

import json
import subprocess
from pathlib import Path

BUNDLE = Path("/output/attestation-bundle.json")
VERDICT = Path("/output/gate-verdict.json")
ANCHOR = Path("/data/fixtures/anchor-blobs")
PRIMARY = Path("/data/traces/primary.evt")
BLOB_A = Path("/data/blobs/release-a.bin")
BLOB_B = Path("/data/blobs/release-b.bin")

def _sha256_file(path: Path) -> str:
    result = subprocess.run(
        ["sha256sum", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.split()[0]


def _extend(cur: bytes, payload: str) -> bytes:
    proc = subprocess.run(
        ["sha256sum"],
        input=cur + payload.encode(),
        capture_output=True,
        check=True,
    )
    return bytes.fromhex(proc.stdout.decode().split()[0])


def _load_trace_steps(path: Path) -> list[tuple[int, int, str]]:
    steps: list[tuple[int, int, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        steps.append((row["idx"], row["bank"], row["payload"]))
    return steps


def _roll_forward(events: list[tuple[int, int, str]]) -> dict[int, str]:
    regs: dict[int, bytes] = {0: b"\0" * 32, 1: b"\0" * 32, 7: b"\0" * 32, 8: b"\0" * 32}
    for _idx, bank, payload in events:
        regs[bank] = _extend(regs[bank], payload)
    return {str(k): v.hex() for k, v in regs.items()}


def _load_bundle() -> dict:
    assert BUNDLE.exists(), f"missing {BUNDLE}"
    return json.loads(BUNDLE.read_text(encoding="utf-8"))


def _mask_covers_banks(mask: str, banks: list[int]) -> bool:
    if not mask.startswith("0x"):
        return False
    value = int(mask, 16)
    for bank in banks:
        if (value & (1 << bank)) == 0:
            return False
    return True


def test_u4_bundle_version():
    """Bundle document records schema version 1."""
    payload = _load_bundle()
    assert payload.get("version") == 1


def test_k2_blob_rows():
    """Bundle lists both release blobs with matching digests."""
    payload = _load_bundle()
    by_label = {row["label"]: row["sha256"] for row in payload["blobs"]}
    assert by_label["release-a"] == _sha256_file(BLOB_A)
    assert by_label["release-b"] == _sha256_file(BLOB_B)


def test_m7_register_map():
    """Register map matches the primary trace chain after board refresh."""
    payload = _load_bundle()
    want = _roll_forward(_load_trace_steps(PRIMARY))
    got = payload["registers"]
    for bank in ("0", "1", "7", "8"):
        assert got[bank] == want[bank], bank


def test_p4_trace_digest():
    """trace_sha256 covers the canonical primary trace file."""
    payload = _load_bundle()
    assert payload["trace_sha256"] == _sha256_file(PRIMARY)


def test_q9_envelope_fields():
    """Signed envelope exposes nonce, sig_hex, and pcr_mask."""
    env = _load_bundle()["envelope"]
    assert isinstance(env.get("nonce"), str) and env["nonce"]
    assert isinstance(env.get("sig_hex"), str) and len(env["sig_hex"]) > 32
    assert _mask_covers_banks(str(env.get("pcr_mask", "")), [0, 1, 7, 8])


def test_r3_floor_verdict():
    """Gate verdict records floor lane accept."""
    assert VERDICT.exists(), f"missing {VERDICT}"
    doc = json.loads(VERDICT.read_text(encoding="utf-8"))
    assert doc.get("version") == 1
    assert doc.get("lane") == "floor"
    assert doc.get("result") == "accept"


def test_s6_anchor_intact():
    """Anchor seed blobs still match the pinned checksum manifest."""
    manifest = ANCHOR / "checksums.sha256"
    assert manifest.is_file()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        want_hash, rel = line.split(None, 1)
        rel = rel.strip().removeprefix("./")
        path = ANCHOR / rel
        assert _sha256_file(path) == want_hash, rel


def test_t1_floorcheck_cli():
    """floorcheck exits zero on the regenerated bundle."""
    subprocess.run(
        [
            "/opt/rly/bin/floorcheck",
            "--bundle",
            str(BUNDLE),
            "--verdict",
            str(VERDICT),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
