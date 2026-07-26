"""Verifier tests for hospital sterile tray recall reconciliation outcomes."""

import json
import subprocess
from pathlib import Path

ROOT = Path("/data/fixtures")
OUT = Path("/data/out")
RUN = ["/opt/csp/scripts/run-case.sh"]


def _run(case: str) -> None:
    out_dir = OUT / case
    if out_dir.exists():
        for p in out_dir.iterdir():
            p.unlink()
    subprocess.check_call(RUN + ["--case", case, "--root", str(ROOT)])


def _ledger(case: str) -> list[dict]:
    rows = []
    path = OUT / case / "quarantine_ledger.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _tray_state(case: str, tray: str) -> dict:
    for row in _ledger(case):
        if row["tray_id"] == tray:
            return row
    raise AssertionError(f"missing tray {tray} on {case}")


def _disposition(case: str) -> dict:
    return json.loads((OUT / case / "tray_disposition.json").read_text(encoding="utf-8"))


def _audit_rows(case: str) -> list[dict[str, str]]:
    lines = (OUT / case / "recall_audit.tsv").read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        if line.strip():
            rows.append(dict(zip(header, line.split("\t"), strict=True)))
    return rows


def _lot_blocked(case: str, lot: str) -> int:
    for row in _audit_rows(case):
        if row["lot_id"] == lot:
            return int(row["trays_blocked"])
    raise AssertionError(f"missing lot {lot} on {case}")


def test_v01_post_notice_tray():
    """Recalled lot trays on post-notice cases enter HOLD with LOT_RECALL."""
    _run("case_c0412")
    row = _tray_state("case_c0412", "T-101")
    assert row["state"] == "HOLD"
    assert row["reason_code"] == "LOT_RECALL"


def test_v02_zone_clear_tray():
    """Trays from zones without active recall stay RELEASE."""
    _run("case_c0413")
    row = _tray_state("case_c0413", "T-200")
    assert row["state"] == "RELEASE"
    assert row["reason_code"] == "CLEAR"


def test_v03_cycle_window_tray():
    """Scans after cycle end produce STERILE_GAP holds."""
    _run("case_c0414")
    row = _tray_state("case_c0414", "T-300")
    assert row["state"] == "HOLD"
    assert row["reason_code"] == "STERILE_GAP"


def test_v04_split_set_tray():
    """Child trays inherit parent recall holds on split sets."""
    _run("case_c0415")
    row = _tray_state("case_c0415", "T-402")
    assert row["state"] == "HOLD"
    assert row["reason_code"] == "LOT_RECALL"


def test_v05_rerun_stable():
    """Repeated runs keep ledger and audit bytes stable."""
    _run("case_c0416")
    ledger_a = (OUT / "case_c0416" / "quarantine_ledger.jsonl").read_bytes()
    audit_a = (OUT / "case_c0416" / "recall_audit.tsv").read_bytes()
    _run("case_c0416")
    ledger_b = (OUT / "case_c0416" / "quarantine_ledger.jsonl").read_bytes()
    audit_b = (OUT / "case_c0416" / "recall_audit.tsv").read_bytes()
    assert ledger_a == ledger_b
    assert audit_a == audit_b


def test_v06_audit_blocked_count():
    """Recall audit blocked counts match held trays per lot without inflation."""
    _run("case_c0416")
    assert _lot_blocked("case_c0416", "L-R3") == 2


def test_v07_ledger_contract():
    """Ledger rows expose every field named in the output contract."""
    _run("case_c0412")
    row = _ledger("case_c0412")[0]
    for key in ("tray_id", "state", "reason_code", "source_case", "seq"):
        assert key in row


def test_v08_disposition_contract():
    """Disposition report exposes version and tray entries."""
    _run("case_c0412")
    doc = _disposition("case_c0412")
    assert doc["version"] == 1
    assert isinstance(doc["trays"], list)
    assert doc["trays"]


def test_v09_audit_contract():
    """Recall audit rows expose every column named in the output contract."""
    _run("case_c0412")
    header = (OUT / "case_c0412" / "recall_audit.tsv").read_text(encoding="utf-8").splitlines()[0].split("\t")
    for key in ("lot_id", "trays_blocked", "trays_cleared", "exposure_class"):
        assert key in header
    for row in _audit_rows("case_c0412"):
        if row["lot_id"] == "L-R1":
            assert row["exposure_class"] == "CLASS_A"


def test_v10_dual_tray_case():
    """Dual-tray case holds both trays while audit clears stay zero."""
    _run("case_c0416")
    assert _tray_state("case_c0416", "T-501")["state"] == "HOLD"
    assert _tray_state("case_c0416", "T-502")["state"] == "HOLD"
    for row in _audit_rows("case_c0416"):
        if row["lot_id"] == "L-R3":
            assert int(row["trays_cleared"]) == 0


def test_v11_snap_hold_tray():
    """Snapshot-held trays stay on HOLD regardless of lot signals."""
    _run("case_c0417")
    row = _tray_state("case_c0417", "T-601")
    assert row["state"] == "HOLD"
    assert row["reason_code"] == "SNAP_HOLD"


def test_v12_notice_timing_tray():
    """Notices effective after case start must not block release."""
    _run("case_c0418")
    row = _tray_state("case_c0418", "T-701")
    assert row["state"] == "RELEASE"
    assert row["reason_code"] == "CLEAR"
