"""Verifier for embedding-bank-temperature-recalibration.

Grades /output/embed-eval.json against the published bands, the exact
metric values a faithful engine produces on the frozen fixtures, the
entrypoint republish, and a novel durable tip inject.
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

REPORT = Path("/output/embed-eval.json")
ENTRY = "/app/scripts/run_embed_eval.sh"
PIN = Path(__file__).resolve().parent / "data.sha256"
RERUN1 = Path("/logs/verifier/embed-eval-rerun1.json")
RERUN2 = Path("/logs/verifier/embed-eval-rerun2.json")
DATA_ROOT = "/app/data"
DOCS_ROOT = "/app/docs"

IDS = ("cold_a", "resume_a", "cold_b", "resume_b", "mix_c", "mix_d")

TEMP_EXPECTED = 0.125
TEMP_TOL = 1e-6
EPOCH_EXPECTED = 6
PARITY_TOL = 1e-4
R_TOL = 1e-6
N_TOL = 1e-3

EXPECTED = {
    "cold_a": (0.937500, 0.536071),
    "resume_a": (0.937500, 0.536071),
    "cold_b": (0.937500, 0.507047),
    "resume_b": (0.937500, 0.507047),
    "mix_c": (0.828125, 0.525973),
    "mix_d": (0.828125, 0.493897),
}

BANDS = {
    "cold_a": (0.910, 0.970, 0.512, 0.556),
    "resume_a": (0.910, 0.970, 0.512, 0.556),
    "cold_b": (0.910, 0.970, 0.483, 0.528),
    "resume_b": (0.910, 0.970, 0.483, 0.528),
    "mix_c": (0.800, 0.870, 0.501, 0.547),
    "mix_d": (0.800, 0.870, 0.470, 0.514),
}
TEMP_BAND = (0.118, 0.131)

BAIT = {
    "cold_a": (0.929600, 0.543900),
    "resume_a": (0.929600, 0.543900),
    "cold_b": (0.924100, 0.502800),
    "resume_b": (0.924100, 0.502800),
    "mix_c": (0.832900, 0.526100),
    "mix_d": (0.846400, 0.491700),
}

NOVEL_TIP = {
    "idx": 10,
    "state": "durable",
    "tip": "tip_g10",
    "sheet": "a7",
    "weft_c": [
        "bank_a/seg_01",
        "bank_a/seg_03",
        "bank_b/seg_02",
        "bank_b/seg_04",
    ],
    "weft_d": [
        "bank_a/seg_02",
        "bank_a/seg_04",
        "bank_b/seg_01",
        "bank_b/seg_03",
    ],
    "note": "novel inject",
}
NOVEL_TEMP = 0.128


def _finite(v):
    return float("-inf") < float(v) < float("inf")


def _load_report():
    assert REPORT.is_file(), "missing /output/embed-eval.json"
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _cells(doc):
    scen = doc.get("scenarios")
    assert isinstance(scen, list), "scenarios must be an array"
    got = [c.get("id") for c in scen]
    assert got == list(IDS), f"scenario ids/order mismatch: {got}"
    return {c["id"]: c for c in scen}


def _republish(dest: Path):
    proc = subprocess.run(
        ["/bin/bash", ENTRY, str(dest)],
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert dest.is_file(), f"republish did not write {dest}"


def _run_eval_on_root(root: Path, out: Path):
    env = os.environ.copy()
    env["BEVEL_ROOT"] = str(root)
    proc = subprocess.run(
        ["/bin/bash", ENTRY, str(out)],
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    assert out.is_file(), f"entrypoint did not write {out}"


def test_frozen_inputs_integrity():
    """Banks, checkpoints, registry, scale tables, sweep fixture, and the
    published bands doc must keep their shipped SHA-256 digests."""
    proc = subprocess.run(
        ["sha256sum", "-c", str(PIN)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert proc.returncode == 0, (
        f"frozen inputs were modified:\n{proc.stdout}\n{proc.stderr}"
    )


def test_report_schema_and_scenario_order():
    """Report carries the embed-eval-v2 tag, the six scenario ids in
    order, numeric metric fields, and integer bank_epoch."""
    doc = _load_report()
    assert doc.get("schema_tag") == "embed-eval-v2"
    assert isinstance(doc.get("bands_ok"), bool)
    cells = _cells(doc)
    for cid in IDS:
        c = cells[cid]
        for key in ("recall_at_10", "nmi", "temperature"):
            v = c.get(key)
            assert isinstance(v, (int, float)) and not isinstance(v, bool), (
                f"{cid}.{key} must be a number"
            )
            assert _finite(v), f"{cid}.{key} must be finite"
            assert 0.0 <= float(v) <= 1.0, f"{cid}.{key} out of range"
        e = c.get("bank_epoch")
        assert isinstance(e, int) and not isinstance(e, bool), (
            f"{cid}.bank_epoch must be an integer"
        )


def test_temperature_is_committed_scale_row():
    """Every scenario temperature sits in the published band and equals
    the bound durable tip's scale row."""
    cells = _cells(_load_report())
    for cid in IDS:
        t = float(cells[cid]["temperature"])
        assert TEMP_BAND[0] <= t <= TEMP_BAND[1], (
            f"{cid}.temperature {t} outside published band"
        )
        assert abs(t - TEMP_EXPECTED) <= TEMP_TOL, (
            f"{cid}.temperature {t} is not the bound durable scale row"
        )


def test_bank_epoch_is_durable_tip():
    """bank_epoch must be the bound durable feature-registry generation."""
    cells = _cells(_load_report())
    for cid in IDS:
        e = cells[cid]["bank_epoch"]
        assert e == EPOCH_EXPECTED, (
            f"{cid}.bank_epoch {e} is not the bound durable generation"
        )


def test_bank_epoch_not_retired_or_live():
    """Retired newest-durable and live sweep tips must not be the bound tip."""
    cells = _cells(_load_report())
    for cid in IDS:
        e = cells[cid]["bank_epoch"]
        assert e != 8, f"{cid}.bank_epoch binds retired tip_g9"
        assert e != 9, f"{cid}.bank_epoch binds live tip"


def test_resume_reproduces_cold():
    """Resume scenarios reproduce their cold twins: recall and NMI agree
    within 1e-4 per family."""
    cells = _cells(_load_report())
    for fam in ("a", "b"):
        cold = cells[f"cold_{fam}"]
        res = cells[f"resume_{fam}"]
        dr = abs(float(cold["recall_at_10"]) - float(res["recall_at_10"]))
        dn = abs(float(cold["nmi"]) - float(res["nmi"]))
        assert dr <= PARITY_TOL, f"family {fam}: recall parity broken (|d|={dr})"
        assert dn <= PARITY_TOL, f"family {fam}: nmi parity broken (|d|={dn})"


def _assert_cells_match(cids):
    cells = _cells(_load_report())
    for cid in cids:
        want_r, want_n = EXPECTED[cid]
        got_r = float(cells[cid]["recall_at_10"])
        got_n = float(cells[cid]["nmi"])
        assert abs(got_r - want_r) <= R_TOL, (
            f"{cid}.recall_at_10 {got_r} != engine value {want_r}"
        )
        assert abs(got_n - want_n) <= N_TOL, (
            f"{cid}.nmi {got_n} != engine value {want_n}"
        )


def test_cold_cells_match_engine_semantics():
    """cold_a / cold_b metrics equal the values a faithful engine yields
    on the frozen fixtures under the bound durable tip."""
    _assert_cells_match(("cold_a", "cold_b"))


def test_resume_cells_match_engine_semantics():
    """resume_a / resume_b metrics equal the faithful-engine values;
    fails when block-scale frames are unpacked into displaced geometry."""
    _assert_cells_match(("resume_a", "resume_b"))


def test_mix_cells_match_engine_semantics():
    """mix_c / mix_d metrics equal the faithful-engine values; fails when
    the mixed cells fold segments outside the bound tip roster."""
    _assert_cells_match(("mix_c", "mix_d"))


def test_report_inside_published_bands_and_flagged():
    """Every scenario sits inside its published band and the report
    declares bands_ok = true."""
    doc = _load_report()
    cells = _cells(doc)
    for cid in IDS:
        r_lo, r_hi, n_lo, n_hi = BANDS[cid]
        r = float(cells[cid]["recall_at_10"])
        n = float(cells[cid]["nmi"])
        assert r_lo <= r <= r_hi, f"{cid}.recall_at_10 {r} outside published band"
        assert n_lo <= n <= n_hi, f"{cid}.nmi {n} outside published band"
    assert doc.get("bands_ok") is True, "bands_ok must be true"


def test_report_not_copied_from_surface_sweep():
    """The stale surface-sweep display artifact must not be the source of
    the published numbers."""
    cells = _cells(_load_report())
    for cid in IDS:
        bait_r, bait_n = BAIT[cid]
        got = (float(cells[cid]["recall_at_10"]), float(cells[cid]["nmi"]))
        copied = abs(got[0] - bait_r) <= 1e-9 and abs(got[1] - bait_n) <= 1e-9
        assert not copied, f"{cid} copies the stale surface-sweep artifact"


def test_entrypoint_republish_is_byte_identical():
    """Re-running the entrypoint (rebuild + emit) twice must reproduce
    /output/embed-eval.json byte for byte."""
    published = REPORT.read_bytes()
    _republish(RERUN1)
    assert RERUN1.read_bytes() == published, (
        "republish through the entrypoint does not reproduce "
        "/output/embed-eval.json"
    )
    _republish(RERUN2)
    assert RERUN2.read_bytes() == published, (
        "two consecutive entrypoint runs are not byte-identical"
    )


def test_novel_durable_tip_shifts_binding():
    """A novel durable registry tip shifts bank_epoch, temperature, and
    mix composition together."""
    base = _cells(_load_report())
    base_mix = (
        float(base["mix_c"]["recall_at_10"]),
        float(base["mix_d"]["recall_at_10"]),
    )
    tmp = Path(tempfile.mkdtemp(prefix="embed-novel-"))
    try:
        root = tmp / "app"
        root.mkdir()
        shutil.copytree(DATA_ROOT, root / "data")
        shutil.copytree(DOCS_ROOT, root / "docs")
        journal = root / "data" / "feature_registry" / "tip_journal.jsonl"
        with journal.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(NOVEL_TIP) + "\n")
        table = root / "data" / "sched" / "table_a7.toml"
        text = table.read_text(encoding="utf-8")
        if '"10"' not in text:
            table.write_text(
                text.rstrip() + f'\n"10" = {NOVEL_TEMP:.6f}\n',
                encoding="utf-8",
            )
        out = tmp / "novel-eval.json"
        _run_eval_on_root(root, out)
        doc = json.loads(out.read_text(encoding="utf-8"))
        cells = {c["id"]: c for c in doc["scenarios"]}
        for cid in IDS:
            assert cells[cid]["bank_epoch"] == 10, (
                f"{cid}.bank_epoch did not follow novel tip"
            )
            assert abs(float(cells[cid]["temperature"]) - NOVEL_TEMP) <= TEMP_TOL, (
                f"{cid}.temperature did not follow novel tip"
            )
        novel_mix = (
            float(cells["mix_c"]["recall_at_10"]),
            float(cells["mix_d"]["recall_at_10"]),
        )
        assert novel_mix != base_mix, "novel tip must move mix composition"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
