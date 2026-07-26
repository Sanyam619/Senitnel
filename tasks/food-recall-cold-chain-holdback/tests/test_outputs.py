"""Verifier tests for cold-chain holdback batch outcomes."""

import json
import subprocess
from pathlib import Path

ROOT = Path("/data/fixtures")
OUT = Path("/data/out")
RUN = ["/opt/distro/scripts/run-cycle.sh"]
REBUILD = [str(Path(RUN[0]).parent / "offline-rebuild.sh")]


def _ensure_rebuilt() -> None:
    """Pick up Java source edits before each cycle run."""
    subprocess.check_call(REBUILD)


def _run(day: str) -> None:
    _ensure_rebuilt()
    out_dir = OUT / day
    if out_dir.exists():
        for p in out_dir.iterdir():
            p.unlink()
    subprocess.check_call(RUN + ["--day", day, "--root", str(ROOT)])


def _ledger(day: str) -> list[dict]:
    rows = []
    for line in (OUT / day / "holdback_ledger.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _ledger_row(day: str, unit: str) -> dict:
    for row in _ledger(day):
        if row["unit_id"] == unit:
            return row
    raise AssertionError(f"missing ledger row for {unit} on {day}")


def _state(day: str, unit: str) -> str:
    return _ledger_row(day, unit)["state"]


def _audit(day: str) -> dict:
    return json.loads((OUT / day / "release_auth_audit.json").read_text(encoding="utf-8"))


def _audit_entries(day: str, unit: str) -> list[dict]:
    return [entry for entry in _audit(day)["entries"] if entry["unit_id"] == unit]


def _tsv_data(day: str) -> list[dict]:
    text = (OUT / day / "affected_units.tsv").read_text(encoding="utf-8").strip()
    if not text:
        return []
    rows = [line.split("\t") for line in text.splitlines()]
    header = rows[0]
    return [dict(zip(header, row, strict=True)) for row in rows[1:]]


def _assert_ledger(day: str, unit: str, *, state: str, reason_code: str) -> None:
    row = _ledger_row(day, unit)
    assert row["state"] == state
    assert row["reason_code"] == reason_code
    tags = {entry["source_day"] for entry in _ledger(day)}
    assert len(tags) == 1, f"source_day must be stable on {day}"


def _assert_audit(day: str, unit: str, *, auth_id: str, decision: str, precedence_rank: int) -> None:
    matches = _audit_entries(day, unit)
    assert matches, f"missing audit entry for {unit} on {day}"
    entry = matches[0]
    assert entry["auth_id"] == auth_id
    assert entry["decision"] == decision
    assert entry["precedence_rank"] == precedence_rank


def test_k9_active_notice_blocks():
    """Recalled dairy unit stays HELD despite signoff grant."""
    _run("day_r0412")
    assert _state("day_r0412", "LOT-D742") == "HELD"
    assert _state("day_r0412", "LOT-F881") == "RELEASED"


def test_m4_unrelated_release():
    """Unrelated frozen unit releases when probe window is valid."""
    _run("day_r0413")
    assert _state("day_r0413", "LOT-K220") == "RELEASED"


def test_p2_cleared_excursion():
    """Cleared review with signoff releases held excursion case."""
    _run("day_r0414")
    assert _state("day_r0414", "LOT-T119") == "RELEASED"


def test_q7_split_lineage():
    """Both dock-split children stay HELD when parent flagged."""
    _run("day_r0415")
    assert _state("day_r0415", "LOT-P500A") == "HELD"
    assert _state("day_r0415", "LOT-P500B") == "HELD"


def test_s3_rerun_stable():
    """Two consecutive runs stay byte-stable and keep split children held."""
    _run("day_r0415")
    assert _state("day_r0415", "LOT-P500A") == "HELD"
    assert _state("day_r0415", "LOT-P500B") == "HELD"
    ledger_a = (OUT / "day_r0415" / "holdback_ledger.jsonl").read_bytes()
    tsv_a = (OUT / "day_r0415" / "affected_units.tsv").read_bytes()
    audit_a = (OUT / "day_r0415" / "release_auth_audit.json").read_bytes()
    _run("day_r0415")
    assert _state("day_r0415", "LOT-P500A") == "HELD"
    assert _state("day_r0415", "LOT-P500B") == "HELD"
    ledger_b = (OUT / "day_r0415" / "holdback_ledger.jsonl").read_bytes()
    tsv_b = (OUT / "day_r0415" / "affected_units.tsv").read_bytes()
    audit_b = (OUT / "day_r0415" / "release_auth_audit.json").read_bytes()
    assert ledger_a == ledger_b
    assert tsv_a == tsv_b
    assert audit_a == audit_b


def test_w2_hidden_day():
    """Hidden distribution day blocks cross-store recalled unit."""
    _run("day_r0416")
    assert _state("day_r0416", "LOT-H901") == "HELD"
    tsv = (OUT / "day_r0416" / "affected_units.tsv").read_text(encoding="utf-8")
    assert "ST-66" in tsv
    assert "ST-77" in tsv


def test_v4_pipeline_metadata():
    """Cross-store recall day carries matching reason, audit, and extract counts."""
    _run("day_r0416")
    _assert_ledger("day_r0416", "LOT-H901", state="HELD", reason_code="NOTICE_ACTIVE")
    _assert_audit("day_r0416", "LOT-H901", auth_id="SA-9010", decision="GRANT", precedence_rank=1)
    assert _audit("day_r0416")["version"] == 1
    assert _tsv_data("day_r0416") == [
        {
            "unit_id": "LOT-H901",
            "store_id": "ST-66",
            "exposure_class": "NOTICE_ACTIVE",
            "qty_cases": "12",
        },
        {
            "unit_id": "LOT-H901",
            "store_id": "ST-77",
            "exposure_class": "NOTICE_ACTIVE",
            "qty_cases": "8",
        },
    ]
