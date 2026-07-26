"""Verifier tests for the tabular uplift treatment-effect evaluation report."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

REPORT_PATH = "/output/uplift-eval.json"
BINARY_PATH = "/app/eng/target/release/uplift-eval"
DATA_ROOT = Path("/app/data")
CRATE_ROOT = Path("/app/eng")
SCHEMA_TAG = "uplift-eval-v1"
SLICE_ORDER = ("s_alpha", "s_beta", "s_gamma", "s_delta", "s_epsilon")
AUUC_BANDS = {
    "s_alpha": (0.406, 0.418),
    "s_beta": (0.432, 0.444),
    "s_gamma": (0.459, 0.471),
    "s_delta": (0.385, 0.397),
    "s_epsilon": (0.418, 0.430),
}
QINI_BANDS = {
    "s_alpha": (0.262, 0.274),
    "s_beta": (0.285, 0.297),
    "s_gamma": (0.309, 0.321),
    "s_delta": (0.242, 0.254),
    "s_epsilon": (0.273, 0.285),
}
DURABLE_ESTIMATORS = ("ipw", "dr", "tmle")
NOVEL_JOURNAL_ROW = {
    "tip": "tip_n5",
    "epoch": 10,
    "sealed": True,
    "propensity": "tmle",
}


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=False, capture_output=True, text=True, **kwargs)


def _assert_fixtures_intact() -> None:
    proc = _run(["bash", "/app/scripts/verify_fixtures.sh"])
    assert proc.returncode == 0, proc.stderr


def _read_json(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _journal_rows(root: Path) -> list[dict]:
    rows = []
    text = (root / "feature_registry" / "tip_journal.jsonl").read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _retired_tips(root: Path) -> set[str]:
    path = root / "feature_registry" / "retired_tips.jsonl"
    if not path.is_file():
        return set()
    out = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.add(json.loads(line)["tip"])
    return out


def _resolve_tip(rows: list[dict], retired: set[str]) -> dict:
    best = None
    for row in rows:
        if not row.get("sealed"):
            continue
        if row.get("tip") in retired:
            continue
        if best is None or int(row["epoch"]) >= int(best["epoch"]):
            best = row
    assert best is not None, "journal has no selectable sealed tip"
    return best


def _roster(root: Path) -> dict:
    data = _read_json(root / "estimators" / "roster.json")
    return {row["name"]: row["column"] for row in data["estimators"]}


def _mirror_roster(root: Path) -> dict:
    data = _read_json(root / "ledger" / "roster_mirror.json")
    return {row["name"]: row["column"] for row in data["estimators"]}


def _slice_fixtures(root: Path) -> list[dict]:
    rows = []
    for path in sorted((root / "outcomes").glob("*.json")):
        rows.append(_read_json(path))
    rows.sort(key=lambda r: int(r["seq"]))
    return rows


def _column_metrics(fx: dict, column: str) -> tuple[float, float]:
    return float(fx[f"auuc_{column}"]), float(fx[f"qini_{column}"])


def _obs_metrics(fx: dict) -> tuple[float, float]:
    return float(fx["auuc_obs"]), float(fx["qini_obs"])


def _expected_state(root: Path) -> dict:
    tip = _resolve_tip(_journal_rows(root), _retired_tips(root))
    roster = _roster(root)
    column = roster[tip["propensity"]]
    fixtures = _slice_fixtures(root)
    slices = []
    for fx in fixtures:
        auuc, qini = _column_metrics(fx, column)
        slices.append(
            {
                "id": fx["id"],
                "auuc": auuc,
                "qini": qini,
                "treatment_tip": int(tip["epoch"]),
                "propensity": tip["propensity"],
            }
        )
    return {"tip": tip, "column": column, "slices": slices, "fixtures": fixtures}


def _load_report() -> dict:
    _assert_fixtures_intact()
    assert Path(REPORT_PATH).is_file(), "missing /output/uplift-eval.json"
    return _read_json(REPORT_PATH)


def _assert_bands(report: dict) -> None:
    by_id = {row["id"]: row for row in report["slices"]}
    for sid, (lo, hi) in AUUC_BANDS.items():
        auuc = float(by_id[sid]["auuc"])
        assert lo <= auuc <= hi, f"{sid} auuc {auuc} outside [{lo}, {hi}]"
    for sid, (lo, hi) in QINI_BANDS.items():
        qini = float(by_id[sid]["qini"])
        assert lo <= qini <= hi, f"{sid} qini {qini} outside [{lo}, {hi}]"
    assert report["eval_ok"] is True


def test_a3_garnet():
    """Frozen outcomes, treatments, features, and registry match fixtures.sha256."""
    _assert_fixtures_intact()


def test_b7_zircon():
    """Report advertises schema_tag, slice order, and required slice fields."""
    report = _load_report()
    assert report.get("schema_tag") == SCHEMA_TAG
    assert isinstance(report.get("eval_ok"), bool)
    slices = report.get("slices")
    assert isinstance(slices, list) and slices
    ids = [row["id"] for row in slices]
    assert ids == list(SLICE_ORDER)
    for row in slices:
        assert set(row) >= {"id", "auuc", "qini", "treatment_tip", "propensity"}
        assert isinstance(row["id"], str)
        assert float("-inf") < float(row["auuc"]) < float("inf")
        assert float("-inf") < float(row["qini"]) < float("inf")
        assert not isinstance(row["treatment_tip"], (str, bool))
        assert float(row["treatment_tip"]) == int(row["treatment_tip"])
        assert isinstance(row["propensity"], str)


def test_c1_biotite():
    """treatment_tip on every slice carries the sealed, non-retired resolved epoch."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    for row in report["slices"]:
        assert int(row["treatment_tip"]) == int(state["tip"]["epoch"])


def test_d9_epidote():
    """Published tip is neither the retired sealed-max nor the live observational epoch."""
    report = _load_report()
    rows = _journal_rows(DATA_ROOT)
    retired = _retired_tips(DATA_ROOT)
    sealed_max = max(
        (row for row in rows if row.get("sealed")),
        key=lambda r: int(r["epoch"]),
    )
    assert sealed_max["tip"] in retired, "fixture must bait sealed-max with a retired tip"
    live_epochs = {int(row["epoch"]) for row in rows if row["tip"] == "tip_live"}
    state = _expected_state(DATA_ROOT)
    assert int(state["tip"]["epoch"]) != int(sealed_max["epoch"])
    assert int(state["tip"]["epoch"]) not in live_epochs
    published = {int(row["treatment_tip"]) for row in report["slices"]}
    assert published == {int(state["tip"]["epoch"])}
    assert int(sealed_max["epoch"]) not in published
    assert not (published & live_epochs)


def test_e2_scoria():
    """propensity on every slice is the durable estimator from the tip, not surface."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    want = state["tip"]["propensity"]
    assert want in DURABLE_ESTIMATORS
    for row in report["slices"]:
        assert row["propensity"] == want


def test_f5_dolomite():
    """Per-slice auuc and qini match the roster-assigned scored column."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    by_id = {row["id"]: row for row in report["slices"]}
    for want in state["slices"]:
        got = by_id[want["id"]]
        assert abs(float(got["auuc"]) - want["auuc"]) <= 1e-6
        assert abs(float(got["qini"]) - want["qini"]) <= 1e-6


def test_g8_feldspar():
    """Every slice lands inside its published band and eval_ok is true."""
    _assert_bands(_load_report())


def test_i6_marl():
    """Observational mean-difference path misses at least one published AUUC band."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    fixtures_by_id = {fx["id"]: fx for fx in state["fixtures"]}
    first_id = SLICE_ORDER[0]
    by_id = {row["id"]: row for row in report["slices"]}
    got = float(by_id[first_id]["auuc"])
    lo, hi = AUUC_BANDS[first_id]
    assert lo <= got <= hi
    obs_auuc, _ = _obs_metrics(fixtures_by_id[first_id])
    assert not (lo <= obs_auuc <= hi), "fixture must make the observational path miss auuc band"
    assert abs(got - obs_auuc) > 1e-6


def test_n8_basalt():
    """The stale ledger roster copy is not the scored-column authority."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    estimator = state["tip"]["propensity"]
    stale = _mirror_roster(DATA_ROOT)[estimator]
    assert stale != state["column"], "fixture must keep a divergent mirror mapping"
    fixtures_by_id = {fx["id"]: fx for fx in state["fixtures"]}
    by_id = {row["id"]: row for row in report["slices"]}
    for sid in SLICE_ORDER:
        stale_auuc, stale_qini = _column_metrics(fixtures_by_id[sid], stale)
        alo, ahi = AUUC_BANDS[sid]
        qlo, qhi = QINI_BANDS[sid]
        assert not (alo <= stale_auuc <= ahi and qlo <= stale_qini <= qhi)
        assert abs(float(by_id[sid]["auuc"]) - stale_auuc) > 1e-6
        assert abs(float(by_id[sid]["qini"]) - stale_qini) > 1e-6


def test_h4_gneiss():
    """The real report is not the pre-baked surface_ok.json bait."""
    report = _load_report()
    bait = _read_json(DATA_ROOT / "fixtures" / "surface_ok.json")
    assert report != bait
    assert report["slices"] != bait["slices"]
    _assert_bands(report)


def test_j0_schist():
    """Verifier rebuild from /app/eng re-emits a matching in-band report."""
    _assert_fixtures_intact()
    before = Path(REPORT_PATH).read_bytes()
    build = _run(
        ["cargo", "build", "--release", "--offline", "--locked"],
        cwd=str(CRATE_ROOT),
    )
    assert build.returncode == 0, build.stderr
    fd, tmp = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        run = _run([BINARY_PATH, "--data", str(DATA_ROOT), "--out", tmp])
        assert run.returncode == 0, run.stderr
        after = Path(tmp).read_bytes()
        assert after == before
        _assert_bands(json.loads(after.decode("utf-8")))
    finally:
        os.unlink(tmp)


def test_k3_pumice():
    """Two consecutive eval runs produce byte-identical in-band JSON."""
    _assert_fixtures_intact()
    fd1, p1 = tempfile.mkstemp(suffix=".json")
    fd2, p2 = tempfile.mkstemp(suffix=".json")
    os.close(fd1)
    os.close(fd2)
    try:
        for path in (p1, p2):
            run = _run([BINARY_PATH, "--data", str(DATA_ROOT), "--out", path])
            assert run.returncode == 0, run.stderr
        assert Path(p1).read_bytes() == Path(p2).read_bytes()
        _assert_bands(_read_json(p1))
    finally:
        os.unlink(p1)
        os.unlink(p2)


def test_l7_dunite():
    """A novel sealed tip moves treatment_tip, propensity, and the scored column."""
    _assert_fixtures_intact()
    tmp_root = Path(tempfile.mkdtemp(prefix="uplift-novel-"))
    try:
        shutil.copytree(DATA_ROOT / "outcomes", tmp_root / "outcomes")
        shutil.copytree(DATA_ROOT / "feature_registry", tmp_root / "feature_registry")
        shutil.copytree(DATA_ROOT / "estimators", tmp_root / "estimators")
        shutil.copytree(DATA_ROOT / "ledger", tmp_root / "ledger")
        journal = tmp_root / "feature_registry" / "tip_journal.jsonl"
        with open(journal, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(NOVEL_JOURNAL_ROW) + "\n")

        base_state = _expected_state(DATA_ROOT)
        state = _expected_state(tmp_root)
        assert int(state["tip"]["epoch"]) == int(NOVEL_JOURNAL_ROW["epoch"])
        assert state["tip"]["propensity"] == NOVEL_JOURNAL_ROW["propensity"]
        assert int(state["tip"]["epoch"]) != int(base_state["tip"]["epoch"])
        assert state["column"] != base_state["column"]

        fd, out = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            run = _run([BINARY_PATH, "--data", str(tmp_root), "--out", out])
            assert run.returncode == 0, run.stderr
            report = _read_json(out)
            by_id = {row["id"]: row for row in report["slices"]}
            base_by_id = {row["id"]: row for row in base_state["slices"]}
            for want in state["slices"]:
                got = by_id[want["id"]]
                assert int(got["treatment_tip"]) == int(state["tip"]["epoch"])
                assert got["propensity"] == state["tip"]["propensity"]
                assert abs(float(got["auuc"]) - want["auuc"]) <= 1e-6
                assert abs(float(got["qini"]) - want["qini"]) <= 1e-6
                base_row = base_by_id[want["id"]]
                assert abs(float(got["auuc"]) - base_row["auuc"]) > 1e-6
                assert abs(float(got["qini"]) - base_row["qini"]) > 1e-6
        finally:
            os.unlink(out)
    finally:
        shutil.rmtree(tmp_root)


def test_m2_andesite():
    """Durable tip bind receipt must name the registry-resolved tip and estimator."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    accept = Path("/app/calib/tip_bind.accept")
    assert accept.is_file(), "serving tip bind receipt must exist after seating"
    pairs = {}
    for line in accept.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        pairs[key.strip()] = value.strip().strip('"')
    assert pairs.get("tip") == state["tip"]["tip"]
    assert pairs.get("epoch") == str(int(state["tip"]["epoch"]))
    assert pairs.get("propensity") == state["tip"]["propensity"]
    for row in report["slices"]:
        assert row["propensity"] == pairs["propensity"]
        assert int(row["treatment_tip"]) == int(pairs["epoch"])
