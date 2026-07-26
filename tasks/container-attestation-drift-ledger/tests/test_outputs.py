"""Verifier for container attestation drift ledger repair."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPORT = Path("/output/drift-report.json")
ANCHOR = Path("/data/fixtures/anchors/manifest.sha256")
DATA = Path("/data")
STORE = DATA / "store"
JOURNAL = DATA / "journal"
POLICY = DATA / "policy" / "roots.toml"
ATTEST = DATA / "attest"
VAR = Path("/app/var")
LEDGER = VAR / "ledger.jsonl"
CHECK = VAR / "check.json"
GATE = VAR / "gate.json"

_PIPELINE_REPORT: dict | None = None


def _frontier_epoch() -> int:
    text = POLICY.read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("frontier_epoch"):
            return int(line.split("=", 1)[1].strip())
    raise AssertionError("frontier_epoch missing from policy roots")


def _journal_rows() -> list[dict]:
    rows: list[dict] = []
    for path in sorted(JOURNAL.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    assert rows, "promotion journal is empty"
    return rows


def _platform_digest(store_key: str) -> str:
    doc = json.loads((STORE / store_key / "platform.json").read_text(encoding="utf-8"))
    return doc["digest"]


def _expected() -> dict[str, dict]:
    """Admit requires frontier clearance plus subject-bound platform digest.

    The attestation fixture `ok` field is intentionally ignored here.
    """
    frontier = _frontier_epoch()
    out: dict[str, dict] = {}
    for row in _journal_rows():
        ref = row["ref"]
        digest = _platform_digest(row["store_key"])
        out[ref] = {
            "digest": digest,
            "stage": row["stage"],
            "admit": int(row["epoch"]) >= frontier,
            "epoch": int(row["epoch"]),
            "store_key": row["store_key"],
        }
    return out


def _assert_fixture_anchors_intact() -> None:
    recorded = ANCHOR.read_text(encoding="utf-8").strip()
    assert len(recorded) == 64
    files = sorted(
        p for p in DATA.rglob("*") if p.is_file() and "anchors" not in p.parts
    )
    proc = subprocess.run(
        ["openssl", "dgst", "-sha256", "-binary"],
        input=b"".join(p.read_bytes() for p in files),
        check=True,
        capture_output=True,
    )
    live = proc.stdout.hex()
    assert live == recorded


def _rebuild_from_sources() -> None:
    """Compile current /app sources so a hand-written report cannot bypass fixes."""
    script = Path("/app/scripts/rebuild-tools.sh")
    assert script.is_file(), "missing /app/scripts/rebuild-tools.sh"
    subprocess.run(["bash", "/app/scripts/rebuild-tools.sh"], check=True)


def _rerun_replay_pipeline() -> dict:
    """Discard outputs and regenerate via binaries freshly built from /app sources."""
    global _PIPELINE_REPORT
    if _PIPELINE_REPORT is not None:
        return _PIPELINE_REPORT

    _rebuild_from_sources()
    VAR.mkdir(parents=True, exist_ok=True)
    for path in (REPORT, LEDGER, CHECK, GATE):
        if path.exists():
            path.unlink()
    subprocess.run(["/app/bin/replayctl"], check=True)
    assert json.loads(REPORT.read_text(encoding="utf-8"))["version"] == 1
    assert LEDGER.is_file(), "missing /app/var/ledger.jsonl after replay"
    assert CHECK.is_file(), "missing /app/var/check.json after replay"
    assert GATE.is_file(), "missing /app/var/gate.json after replay"
    _PIPELINE_REPORT = json.loads(REPORT.read_text(encoding="utf-8"))
    return _PIPELINE_REPORT


def _images_by_ref(report: dict) -> dict[str, dict]:
    images = report.get("images")
    assert isinstance(images, list)
    out = {}
    for row in images:
        assert isinstance(row, dict)
        ref = row["ref"]
        out[ref] = row
    return out


def _load_ledger() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rows[row["ref"]] = row
    return rows


def _load_check() -> dict[str, dict]:
    rows = json.loads(CHECK.read_text(encoding="utf-8"))
    assert isinstance(rows, list)
    return {row["ref"]: row for row in rows}


def _load_gate() -> dict[str, dict]:
    rows = json.loads(GATE.read_text(encoding="utf-8"))
    assert isinstance(rows, list)
    return {row["ref"]: row for row in rows}


def test_k4_shape_bundle():
    """Report schema, exact promoted ref set, stages, and below-frontier denies."""
    report = _rerun_replay_pipeline()
    assert report.get("version") == 1
    assert isinstance(report.get("images"), list)
    assert isinstance(report.get("mismatches"), list)
    by_ref = _images_by_ref(report)
    expected = _expected()
    frontier = _frontier_epoch()
    assert set(by_ref) == set(expected)
    for ref, exp in expected.items():
        row = by_ref[ref]
        assert isinstance(row.get("ref"), str)
        assert isinstance(row.get("digest"), str)
        assert isinstance(row.get("stage"), str)
        assert isinstance(row.get("admit"), bool)
        assert row["stage"] == exp["stage"]
        if exp["epoch"] < frontier:
            assert row["admit"] is False
    for item in report["mismatches"]:
        assert isinstance(item, dict)
        assert isinstance(item.get("ref"), str)
        assert isinstance(item.get("reason"), str)


def test_m8_slot_matrix():
    """Admit flags require frontier clearance and subject-bound attestation."""
    report = _rerun_replay_pipeline()
    by_ref = _images_by_ref(report)
    expected = _expected()
    check = _load_check()
    gate = _load_gate()
    frontier = _frontier_epoch()
    for ref, exp in expected.items():
        assert by_ref[ref]["admit"] is exp["admit"]
        assert check[ref]["ok"] is True
        assert check[ref]["digest"] == exp["digest"]
        assert gate[ref]["admit"] is (exp["epoch"] >= frontier)
        assert by_ref[ref]["admit"] is (gate[ref]["admit"] and check[ref]["ok"])


def test_p2_hash_align():
    """Ledger and report digests equal the platform content digest."""
    report = _rerun_replay_pipeline()
    by_ref = _images_by_ref(report)
    expected = _expected()
    ledger = _load_ledger()
    for ref, exp in expected.items():
        assert by_ref[ref]["digest"] == exp["digest"]
        assert ledger[ref]["digest"] == exp["digest"]


def test_r6_delta_list():
    """Empty mismatches only when ledger and attestation digests agree."""
    report = _rerun_replay_pipeline()
    assert report.get("mismatches") == []
    by_ref = _images_by_ref(report)
    expected = _expected()
    ledger = _load_ledger()
    check = _load_check()
    for ref, exp in expected.items():
        assert by_ref[ref]["digest"] == exp["digest"]
        assert ledger[ref]["digest"] == check[ref]["digest"] == exp["digest"]


def test_t1_tier_frontier():
    """Stage labels and gate admits respect the post-replay policy frontier."""
    report = _rerun_replay_pipeline()
    by_ref = _images_by_ref(report)
    expected = _expected()
    gate = _load_gate()
    frontier = _frontier_epoch()
    for ref, exp in expected.items():
        assert by_ref[ref]["stage"] == exp["stage"]
        assert by_ref[ref]["admit"] is exp["admit"]
        assert gate[ref]["admit"] is (exp["epoch"] >= frontier)


def test_w3_cross_agree():
    """Tool-produced digests agree and fixture trees under /data stay intact."""
    report = _rerun_replay_pipeline()
    by_ref = _images_by_ref(report)
    expected = _expected()
    ledger = _load_ledger()
    check = _load_check()
    for ref, exp in expected.items():
        assert by_ref[ref]["digest"] == exp["digest"]
        assert ledger[ref]["digest"] == exp["digest"]
        assert check[ref]["digest"] == exp["digest"]
        assert check[ref]["ok"] is True
    _assert_fixture_anchors_intact()
