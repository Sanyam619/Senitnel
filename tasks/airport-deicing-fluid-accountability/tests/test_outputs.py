"""Verifier tests for airport deicing fluid accountability outcomes."""

import json
import subprocess
from pathlib import Path

ROOT = Path("/data/fixtures")
FIXTURE_SHIFTS = ROOT / "shifts"
OUT = Path("/data/out")
RUN = ["/opt/ramp/scripts/run-shift.sh"]


def _file_sha256(path: Path) -> str:
    result = subprocess.run(
        ["sha256sum", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.split()[0]


def _run(shift: str) -> None:
    out_dir = OUT / shift
    if out_dir.exists():
        for p in out_dir.iterdir():
            p.unlink()
    subprocess.check_call(RUN + ["--shift", shift, "--root", str(ROOT)])


def _ledger(shift: str) -> list[dict]:
    rows = []
    path = OUT / shift / "fluid_ledger.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _qty(shift: str, craft: str) -> float:
    for row in _ledger(shift):
        if row["aircraft_id"] == craft:
            return float(row["gallons_applied"])
    raise AssertionError(f"missing craft {craft} on {shift}")


def _tank(shift: str, node: str) -> dict:
    doc = json.loads((OUT / shift / "runoff_compliance.json").read_text(encoding="utf-8"))
    for t in doc["tanks"]:
        if t["tank_id"] == node:
            return t
    raise AssertionError(f"missing tank {node}")


def _util_rows(shift: str) -> list[dict[str, str]]:
    lines = (OUT / shift / "truck_utilization_audit.tsv").read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        if line.strip():
            rows.append(dict(zip(header, line.split("\t"), strict=True)))
    return rows


def _truck_pumped(shift: str, truck: str) -> float:
    for row in _util_rows(shift):
        if row["truck_id"] == truck:
            return float(row["gallons_pumped"])
    raise AssertionError(f"missing truck {truck} on {shift}")


def test_f0_fixtures_intact():
    """Packaged shift fixtures under /data/fixtures remain unmodified."""
    manifest = FIXTURE_SHIFTS / ".fixture_checksums.sha256"
    assert manifest.is_file(), manifest
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        want_hash, rel = line.split(None, 1)
        path = FIXTURE_SHIFTS / rel.strip()
        assert path.is_file(), rel
        assert _file_sha256(path) == want_hash, rel


def test_h4_stand_window_credit():
    """Ledger credits only pulses inside the stand window."""
    _run("shift_w1206")
    assert _qty("shift_w1206", "AC101") == 90.0


def test_m2_type4_curve():
    """Type IV effective qty reflects assay percent without collapse."""
    _run("shift_w1207")
    assert abs(_qty("shift_w1207", "AC202") - 144.0) < 0.01


def test_q1_mass_closure():
    """Applied ledger total matches pulse totals scaled by assays."""
    _run("shift_w1208")
    ledger_sum = sum(r["gallons_applied"] for r in _ledger("shift_w1208"))
    assert abs(ledger_sum - 400.0) < 0.01


def test_p9_retention_headroom():
    """Diverted capture keeps primary node within permit."""
    _run("shift_w1209")
    primary = _tank("shift_w1209", "N-P")
    assert primary["within_permit"] is True
    assert abs(primary["gallons_captured"] - 230.0) < 0.01


def test_s7_rerun_stable():
    """Repeated runs keep ledger and utilization audit bytes stable."""
    _run("shift_w1209")
    ledger_a = (OUT / "shift_w1209" / "fluid_ledger.jsonl").read_bytes()
    tsv_a = (OUT / "shift_w1209" / "truck_utilization_audit.tsv").read_bytes()
    _run("shift_w1209")
    ledger_b = (OUT / "shift_w1209" / "fluid_ledger.jsonl").read_bytes()
    tsv_b = (OUT / "shift_w1209" / "truck_utilization_audit.tsv").read_bytes()
    assert ledger_a == ledger_b
    assert tsv_a == tsv_b


def test_n3_utilization_single_pulse():
    """Overlapping stand rows do not inflate truck pump totals."""
    _run("shift_w1210")
    assert abs(_truck_pumped("shift_w1210", "T7") - 600.0) < 0.01
    assert abs(_truck_pumped("shift_w1210", "T8") - 200.0) < 0.01


def test_r2_ledger_contract_fields():
    """Ledger rows expose every field named in the output contract."""
    _run("shift_w1206")
    row = _ledger("shift_w1206")[0]
    for key in ("aircraft_id", "pad_id", "gallons_applied", "fluid_code", "seq"):
        assert key in row


def test_r5_compliance_contract_fields():
    """Compliance report exposes version and tank entries."""
    _run("shift_w1209")
    doc = json.loads((OUT / "shift_w1209" / "runoff_compliance.json").read_text(encoding="utf-8"))
    assert doc["version"] == 1
    assert isinstance(doc["tanks"], list)
    assert doc["tanks"]


def test_w3_hidden_shift():
    """Hidden shift reports both retention nodes with diverted alternate fill."""
    _run("shift_w1210")
    alt = _tank("shift_w1210", "N-X")
    assert alt["within_permit"] is True
    assert abs(alt["gallons_captured"] - 80.0) < 0.01
    assert _qty("shift_w1210", "AC505") > 0
    assert _qty("shift_w1210", "AC506") > 0


def test_u1_split_retention_nodes():
    """Moderate diversion books primary and alternate capture separately."""
    _run("shift_w1211")
    primary = _tank("shift_w1211", "N-P")
    alternate = _tank("shift_w1211", "N-X")
    assert primary["within_permit"] is True
    assert alternate["within_permit"] is True
    assert abs(primary["gallons_captured"] - 65.0) < 0.01
    assert abs(alternate["gallons_captured"] - 40.0) < 0.01


def test_g2_type4_dual_pulse_sum():
    """Two in-window Type IV pulses aggregate without collapsing assay weight."""
    _run("shift_w1212")
    ledger_sum = sum(r["gallons_applied"] for r in _ledger("shift_w1212"))
    assert abs(ledger_sum - 108.0) < 0.01


def test_k1_ledger_seq_increments():
    """Ledger rows carry monotonic seq values per stand emission."""
    _run("shift_w1211")
    rows = _ledger("shift_w1211")
    assert len(rows) == 1
    assert rows[0]["seq"] == 1


def test_y4_util_efficiency_positive():
    """Truck audit rows include a positive efficiency percentage when pumped."""
    _run("shift_w1206")
    rows = _util_rows("shift_w1206")
    assert rows
    assert float(rows[0]["efficiency_pct"]) > 0.0


def test_a6_reports_not_staged():
    """Shift reports land under /data/out, not the rehearsal staging tree."""
    _run("shift_w1206")
    assert (OUT / "shift_w1206" / "fluid_ledger.jsonl").is_file()
    assert not (Path("/data/out/staging") / "shift_w1206" / "fluid_ledger.jsonl").exists()
