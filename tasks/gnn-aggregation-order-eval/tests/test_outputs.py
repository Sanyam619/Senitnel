"""Verifier for gnn-aggregation-order-eval.

Grades /output/gnn-eval.json against published bands, the desk reference
scorer on frozen fixtures, seating refresh under trial/invalid bind,
entrypoint republish, and novel durable tip injects.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

REPORT = Path("/output/gnn-eval.json")
ENTRY = "/app/scripts/run_gnn_eval.sh"
REF_SCORE = Path("/app/eval/ref_score.py")
PIN = Path(__file__).resolve().parent / "data.sha256"
RERUN1 = Path("/logs/verifier/gnn-eval-rerun1.json")
RERUN2 = Path("/logs/verifier/gnn-eval-rerun2.json")
DATA = Path("/app/data")
BANDS_DOC = Path("/app/docs/gnn_bands.md")

PREF = Path("/app/calib/trial_pref.toml")
BIND = Path("/app/calib/tip_bind.accept")
ENG = Path("/app/eng")

SEATING = (
    ENG / "core" / "src" / "braid.rs",
    ENG / "core" / "src" / "lens.rs",
    ENG / "core" / "src" / "weave.rs",
    ENG / "rank" / "src" / "knot.rs",
    ENG / "rank" / "src" / "facet.rs",
)

IDS = ("cold_a", "resume_a", "cold_b", "resume_b", "mix_c", "mix_d")
PARITY_TOL = 1e-4
A_TOL = 1e-5
F_TOL = 1e-5

BANDS = {
    "cold_a": (0.600, 0.640, 0.970, 1.001),
    "resume_a": (0.600, 0.640, 0.970, 1.001),
    "cold_b": (0.600, 0.640, 0.990, 1.001),
    "resume_b": (0.600, 0.640, 0.990, 1.001),
    "mix_c": (0.640, 0.675, 0.990, 1.001),
    "mix_d": (0.560, 0.605, 0.990, 1.001),
}

NOVEL_SPECS = (
    {
        "tip": {
            "idx": 10,
            "state": "durable",
            "tip": "tip_g10",
            "agg": "sum",
            "norm": "degree",
            "sheet": "a7",
            "weft_c": ["graph_01", "graph_03", "graph_05", "graph_07"],
            "weft_d": ["graph_02", "graph_04", "graph_06", "graph_08"],
            "note": "novel inject a",
        },
        "bind": "tip_g10",
        "bands_ok": False,
    },
    {
        "tip": {
            "idx": 11,
            "state": "durable",
            "tip": "tip_g11",
            "agg": "sum",
            "norm": "raw",
            "sheet": "a7",
            "weft_c": ["graph_01", "graph_04", "graph_06", "graph_07"],
            "weft_d": ["graph_02", "graph_03", "graph_05", "graph_08"],
            "note": "novel inject b",
        },
        "bind": "tip_g11",
        "bands_ok": False,
    },
)

SERVING_PREF = """# Evaluation selection for the graph desk.

[evaluation]
selection = "serving"
refresh = "auto"

[desk]
owner = "eval-rotation"
window = "weekly"
"""

TRIAL_PREF = """# Evaluation selection for the graph desk.

[evaluation]
selection = "trial"
refresh = "auto"

[desk]
owner = "eval-rotation"
window = "weekly"
"""


def _finite(v):
    return float("-inf") < float(v) < float("inf")


def _ref_cells(agg, norm, weft_c, weft_d, data_root=DATA):
    payload = {
        "data": str(data_root),
        "agg": agg,
        "norm": norm,
        "weft_c": list(weft_c),
        "weft_d": list(weft_d),
    }
    proc = subprocess.run(
        ["python3", str(REF_SCORE)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    raw = json.loads(proc.stdout)
    return {k: (float(v[0]), float(v[1])) for k, v in raw.items()}


def _bound_tip_row():
    retired = set()
    for line in (DATA / "feature_registry" / "retired_tips.jsonl").read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        retired.add(json.loads(line)["tip"])
    best = None
    for line in (DATA / "feature_registry" / "tip_journal.jsonl").read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if row.get("state") != "durable":
            continue
        if row.get("tip") in retired:
            continue
        if best is None or int(row["idx"]) > int(best["idx"]):
            best = row
    assert best is not None
    sheet = DATA / "sched" / f"table_{best['sheet']}.toml"
    agg = None
    key = f"\"{best['idx']}\""
    for line in sheet.read_text().splitlines():
        line = line.strip()
        if line.startswith(key):
            agg = line.split("=", 1)[1].strip().strip('"')
            break
    assert agg
    return best, agg


def _base_expected():
    tip, agg = _bound_tip_row()
    return tip, agg, _ref_cells(agg, tip["norm"], tip["weft_c"], tip["weft_d"])


def _load_report():
    assert REPORT.is_file(), "missing /output/gnn-eval.json"
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _cells(doc):
    scen = doc.get("scenarios")
    assert isinstance(scen, list), "scenarios must be an array"
    got = [c.get("id") for c in scen]
    assert got == list(IDS), f"scenario ids/order mismatch: {got}"
    return {c["id"]: c for c in scen}


def _assert_parity(cells):
    for fam in ("a", "b"):
        cold = cells[f"cold_{fam}"]
        resume = cells[f"resume_{fam}"]
        assert abs(float(cold["accuracy"]) - float(resume["accuracy"])) <= PARITY_TOL
        assert abs(float(cold["macro_f1"]) - float(resume["macro_f1"])) <= PARITY_TOL


def _assert_expected(cells, expected):
    for cid, (exp_a, exp_f) in expected.items():
        assert abs(float(cells[cid]["accuracy"]) - exp_a) <= A_TOL
        assert abs(float(cells[cid]["macro_f1"]) - exp_f) <= F_TOL


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
    env["LOAM_ROOT"] = str(root)
    proc = subprocess.run(
        ["/bin/bash", ENTRY, str(out)],
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    assert out.is_file(), f"eval did not write {out}"


def _cargo_build():
    proc = subprocess.run(
        ["cargo", "build", "--release", "--offline", "--locked"],
        cwd=str(ENG),
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr


def _snapshot_desk():
    files = {str(p): p.read_bytes() for p in SEATING}
    files[str(PREF)] = PREF.read_bytes()
    files[str(BIND)] = BIND.read_bytes()
    return files


def _restore_desk(snap):
    for path, body in snap.items():
        Path(path).write_bytes(body)
    _cargo_build()


def _seed_body(crate: str, name: str) -> bytes:
    return (ENG / crate / "seeds" / f"{name}_seed.rs.in").read_bytes()


def test_j2_pyrite():
    """Frozen graphs, checkpoints, registry, sheets, and bands keep pinned digests."""
    assert PIN.is_file(), "missing tests/data.sha256"
    proc = subprocess.run(
        ["sha256sum", "-c", str(PIN)],
        capture_output=True,
        text=True,
        cwd="/",
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_k4_agate():
    """Report schema, scenario ids/order, and field types are well-formed."""
    doc = _load_report()
    assert doc.get("schema_tag") == "gnn-eval-v2"
    assert isinstance(doc.get("bands_ok"), bool)
    cells = _cells(doc)
    for cid, cell in cells.items():
        assert isinstance(cell.get("agg"), str) and cell["agg"]
        assert isinstance(cell.get("tip_epoch"), int)
        assert _finite(cell.get("accuracy"))
        assert _finite(cell.get("macro_f1"))
        assert 0.0 <= float(cell["accuracy"]) <= 1.0 + 1e-9
        assert 0.0 <= float(cell["macro_f1"]) <= 1.0 + 1e-9
        del cid


def test_p7_jasper():
    """Cold/resume accuracy and macro_f1 agree within 1e-4 for each family."""
    _assert_parity(_cells(_load_report()))


def test_r3_garnet():
    """Family-a cold/resume cells match the desk reference scorer."""
    _tip, _agg, expected = _base_expected()
    cells = _cells(_load_report())
    _assert_expected(cells, {k: expected[k] for k in ("cold_a", "resume_a")})


def test_t6_beryl():
    """Family-b cold/resume cells match the desk reference scorer."""
    _tip, _agg, expected = _base_expected()
    cells = _cells(_load_report())
    _assert_expected(cells, {k: expected[k] for k in ("cold_b", "resume_b")})


def test_m5_onyx():
    """Mix cells match the reference scorer and sit inside published bands."""
    _tip, _agg, expected = _base_expected()
    cells = _cells(_load_report())
    for cid in ("mix_c", "mix_d"):
        exp_a, exp_f = expected[cid]
        assert abs(float(cells[cid]["accuracy"]) - exp_a) <= A_TOL
        assert abs(float(cells[cid]["macro_f1"]) - exp_f) <= F_TOL
        a_lo, a_hi, f_lo, f_hi = BANDS[cid]
        assert a_lo <= float(cells[cid]["accuracy"]) <= a_hi
        assert f_lo <= float(cells[cid]["macro_f1"]) <= f_hi


def test_w1_topaz():
    """Every scenario reports the durable aggregation tip from the bound sheet."""
    _tip, agg, _expected = _base_expected()
    cells = _cells(_load_report())
    for cell in cells.values():
        assert cell["agg"] == agg
        assert cell["agg"] != "max"
        assert cell["agg"] != "pna"


def test_v8_lazuli():
    """Every tip_epoch equals the durable non-retired journal generation."""
    tip, _agg, _expected = _base_expected()
    cells = _cells(_load_report())
    for cell in cells.values():
        assert int(cell["tip_epoch"]) == int(tip["idx"])


def test_n8_umber():
    """tip_epoch is neither the retired generation nor the live sweep generation."""
    cells = _cells(_load_report())
    for cell in cells.values():
        epoch = int(cell["tip_epoch"])
        assert epoch != 8, "retired tip generation"
        assert epoch != 9, "live tip generation"


def test_d9_quartz():
    """Two consecutive entrypoint runs produce byte-identical reports."""
    _republish(RERUN1)
    _republish(RERUN2)
    assert RERUN1.read_bytes() == RERUN2.read_bytes()
    assert RERUN1.read_bytes() == REPORT.read_bytes()


def test_e2_opal():
    """Entrypoint republish after rebuild matches the shipped report bytes."""
    dest = Path("/logs/verifier/gnn-eval-rebuild.json")
    _republish(dest)
    assert dest.read_bytes() == REPORT.read_bytes()


def test_g6_flint():
    """bands_ok is true and metrics are not copied from the surface fixture."""
    doc = _load_report()
    assert doc.get("bands_ok") is True
    cells = _cells(doc)
    bait = json.loads((DATA / "fixtures" / "surface_ok.json").read_text(encoding="utf-8"))
    bait_cells = {c["id"]: c for c in bait["scenarios"]}
    for cid in IDS:
        assert abs(float(cells[cid]["accuracy"]) - float(bait_cells[cid]["accuracy"])) > 1e-4
        assert abs(float(cells[cid]["macro_f1"]) - float(bait_cells[cid]["macro_f1"])) > 1e-4
        a_lo, a_hi, f_lo, f_hi = BANDS[cid]
        assert a_lo <= float(cells[cid]["accuracy"]) <= a_hi
        assert f_lo <= float(cells[cid]["macro_f1"]) <= f_hi
    assert BANDS_DOC.is_file()


def test_h3_jade():
    """Trial selection rematerializes seating surfaces from desk seeds on rebuild."""
    snap = _snapshot_desk()
    try:
        probe = SEATING[0]
        probe.write_text(probe.read_text(encoding="utf-8") + "\n// refresh_probe\n", encoding="utf-8")
        PREF.write_text(TRIAL_PREF, encoding="utf-8")
        _cargo_build()
        assert probe.read_bytes() == _seed_body("core", "braid")
        assert b"refresh_probe" not in probe.read_bytes()
    finally:
        _restore_desk(snap)


def test_h4_amber():
    """Live or retired tip bind receipts rematerialize seating on rebuild."""
    snap = _snapshot_desk()
    try:
        PREF.write_text(SERVING_PREF, encoding="utf-8")
        for bad in ("tip_live", "tip_g9"):
            probe = SEATING[3]
            probe.write_text(probe.read_text(encoding="utf-8") + "\n// bind_probe\n", encoding="utf-8")
            BIND.write_text(bad + "\n", encoding="utf-8")
            _cargo_build()
            assert probe.read_bytes() == _seed_body("rank", "knot")
            assert b"bind_probe" not in probe.read_bytes()
    finally:
        _restore_desk(snap)


def test_h5_slate():
    """Publishable serving bind keeps seating durable across a rebuild."""
    snap = _snapshot_desk()
    try:
        tip, _agg = _bound_tip_row()
        PREF.write_text(SERVING_PREF, encoding="utf-8")
        BIND.write_text(tip["tip"] + "\n", encoding="utf-8")
        before = {str(p): p.read_bytes() for p in SEATING}
        _cargo_build()
        for p in SEATING:
            assert p.read_bytes() == before[str(p)]
            crate = "core" if "/core/" in str(p) else "rank"
            assert p.read_bytes() != _seed_body(crate, p.stem)
    finally:
        _restore_desk(snap)


def test_s4_coral():
    """Novel durable tips move agg, epoch, and all scenario metrics with the tip."""
    base_cells = _cells(_load_report())
    for i, case in enumerate(NOVEL_SPECS):
        tip = case["tip"]
        expected = _ref_cells(tip["agg"], tip["norm"], tip["weft_c"], tip["weft_d"])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree("/app/data", root / "data")
            shutil.copytree("/app/calib", root / "calib")
            shutil.copytree("/app/docs", root / "docs")
            journal = root / "data" / "feature_registry" / "tip_journal.jsonl"
            with journal.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(tip, separators=(",", ":")) + "\n")
            (root / "calib" / "tip_bind.accept").write_text(case["bind"] + "\n", encoding="utf-8")
            (root / "calib" / "trial_pref.toml").write_text(SERVING_PREF, encoding="utf-8")
            out = Path("/tmp") / f"gnn_n{i}.json"
            _run_eval_on_root(root, out)
            doc = json.loads(out.read_text(encoding="utf-8"))
            cells = _cells(doc)
            assert doc.get("bands_ok") is case["bands_ok"]
            for cell in cells.values():
                assert cell["agg"] == tip["agg"]
                assert int(cell["tip_epoch"]) == int(tip["idx"])
            _assert_parity(cells)
            _assert_expected(cells, expected)
            for cid in IDS:
                assert abs(float(cells[cid]["accuracy"]) - float(base_cells[cid]["accuracy"])) > 1e-4
