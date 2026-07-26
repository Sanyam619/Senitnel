"""Verifier tests for rare book quarantine circulation outcomes."""

import json
import subprocess
from pathlib import Path

ROOT = Path("/data/fixtures")
OUT = Path("/data/out")
RUN = ["/opt/archives/scripts/run-cycle.sh"]


def _run(day: str) -> None:
    out_dir = OUT / day
    if out_dir.exists():
        for p in out_dir.iterdir():
            p.unlink()
    subprocess.check_call(RUN + ["--day", day, "--root", str(ROOT)])


def _ledger(day: str) -> list[dict]:
    rows = []
    for line in (OUT / day / "loan_decision_ledger.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _decision(day: str, volume: str) -> str:
    for row in _ledger(day):
        if row["volume_id"] == volume:
            return row["decision"]
    raise AssertionError(f"missing volume {volume} on {day}")


def _ledger_row(day: str, volume: str) -> dict:
    for row in _ledger(day):
        if row["volume_id"] == volume:
            return row
    raise AssertionError(f"missing volume {volume} on {day}")


def test_k9_active_flag_blocks():
    """Flagged rare volume stays DENIED_LOAN despite covenant grant."""
    _run("day_c0901")
    assert _decision("day_c0901", "VOL-D742") == "DENIED_LOAN"
    assert _decision("day_c0901", "VOL-F881") == "ALLOW"
    flagged = _ledger_row("day_c0901", "VOL-D742")
    assert flagged["reason_code"] == "FLAG_ACTIVE"
    assert "collection_day" in flagged


def test_k9_quarantine_exceptions():
    """Donor covenant grants appear in quarantine_exceptions with versioned entries."""
    _run("day_c0901")
    payload = json.loads(
        (OUT / "day_c0901" / "quarantine_exceptions.json").read_text(encoding="utf-8")
    )
    assert payload["version"] == 1
    assert isinstance(payload["entries"], list)
    assert any(entry.get("decision") == "GRANT" for entry in payload["entries"])


def test_m4_unrelated_release():
    """Unrelated volume allows when sweep window is valid."""
    _run("day_c0902")
    assert _decision("day_c0902", "VOL-K220") == "ALLOW"


def test_p2_cleared_excursion():
    """Cleared exhibit paperwork allows previously held case."""
    _run("day_c0903")
    assert _decision("day_c0903", "VOL-T119") == "ALLOW"


def test_q7_split_lineage():
    """Both bound-volume siblings stay DENIED_LOAN when parent flagged."""
    _run("day_c0904")
    assert _decision("day_c0904", "VOL-P500A") == "DENIED_LOAN"
    assert _decision("day_c0904", "VOL-P500B") == "DENIED_LOAN"


def test_s3_rerun_stable():
    """Two consecutive runs produce identical ledger and TSV bytes."""
    _run("day_c0904")
    ledger_a = (OUT / "day_c0904" / "loan_decision_ledger.jsonl").read_bytes()
    tsv_a = (OUT / "day_c0904" / "shelf_custody_audit.tsv").read_bytes()
    _run("day_c0904")
    ledger_b = (OUT / "day_c0904" / "loan_decision_ledger.jsonl").read_bytes()
    tsv_b = (OUT / "day_c0904" / "shelf_custody_audit.tsv").read_bytes()
    assert ledger_a == ledger_b
    assert tsv_a == tsv_b


def test_w2_hidden_day():
    """Hidden collection day blocks cross-branch flagged volume."""
    _run("day_c0906")
    assert _decision("day_c0906", "VOL-H901") == "DENIED_LOAN"
    tsv = (OUT / "day_c0906" / "shelf_custody_audit.tsv").read_text(encoding="utf-8")
    assert "ST-66" in tsv
    assert "ST-77" in tsv
