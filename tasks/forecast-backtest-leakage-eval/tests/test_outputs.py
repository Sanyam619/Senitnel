"""Verifier tests for the forecasting backtest leakage evaluation report."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

REPORT_PATH = "/output/forecast-eval.json"
BINARY_PATH = "/app/eng/target/release/fc-eval"
DATA_ROOT = Path("/app/data")
CRATE_ROOT = Path("/app/eng")
SCHEMA_TAG = "forecast-eval-v1"
WINDOW_ORDER = ("w_alpha", "w_beta", "w_gamma", "w_delta", "w_epsilon")
SMAPE_BANDS = {
    "w_alpha": (0.136, 0.148),
    "w_beta": (0.150, 0.162),
    "w_gamma": (0.162, 0.174),
    "w_delta": (0.128, 0.140),
    "w_epsilon": (0.145, 0.157),
}
MASE_BANDS = {
    "w_alpha": (0.870, 0.890),
    "w_beta": (0.900, 0.920),
    "w_gamma": (0.935, 0.955),
    "w_delta": (0.850, 0.870),
    "w_epsilon": (0.885, 0.905),
}
NOVEL_JOURNAL_ROW = {
    "tip": "tip_n5",
    "epoch": 10,
    "sealed": True,
    "horizon": 4,
    "scaler": "train_only",
    "shift": 0.02,
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


def _window_fixtures(root: Path) -> list[dict]:
    rows = []
    for path in sorted((root / "series").glob("*.json")):
        rows.append(_read_json(path))
    rows.sort(key=lambda r: int(r["seq"]))
    return rows


def _expected_metrics(fx: dict, tip: dict) -> tuple[float, float]:
    shift = float(tip["shift"])
    smape = float(fx["smape_causal"]) + shift
    mase = float(fx["mase_causal"]) + shift * 0.5
    return smape, mase


def _leak_metrics(fx: dict, tip: dict) -> tuple[float, float]:
    shift = float(tip["shift"])
    smape = float(fx["smape_leak"]) + shift
    mase = float(fx["mase_leak"]) + shift * 0.5
    return smape, mase


def _expected_state(root: Path) -> dict:
    tip = _resolve_tip(_journal_rows(root), _retired_tips(root))
    fixtures = _window_fixtures(root)
    windows = []
    for fx in fixtures:
        smape, mase = _expected_metrics(fx, tip)
        windows.append(
            {
                "id": fx["id"],
                "smape": smape,
                "mase": mase,
                "horizon": int(tip["horizon"]),
                "split_tip": int(tip["epoch"]),
                "scaler": tip["scaler"],
            }
        )
    return {"tip": tip, "windows": windows, "fixtures": fixtures}


def _load_report() -> dict:
    _assert_fixtures_intact()
    assert Path(REPORT_PATH).is_file(), "missing /output/forecast-eval.json"
    return _read_json(REPORT_PATH)


def test_a3_garnet():
    """Frozen series, splits, and registry materials match fixtures.sha256."""
    _assert_fixtures_intact()


def test_b7_zircon():
    """Report advertises schema_tag, window order, and required window fields."""
    report = _load_report()
    assert report.get("schema_tag") == SCHEMA_TAG
    assert isinstance(report.get("eval_ok"), bool)
    windows = report.get("windows")
    assert isinstance(windows, list) and windows
    ids = [row["id"] for row in windows]
    assert ids == list(WINDOW_ORDER)
    for row in windows:
        assert set(row) >= {"id", "smape", "mase", "horizon", "split_tip", "scaler"}
        assert isinstance(row["id"], str)
        assert float("-inf") < float(row["smape"]) < float("inf")
        assert float("-inf") < float(row["mase"]) < float("inf")
        assert isinstance(row["horizon"], int)
        assert isinstance(row["split_tip"], int)
        assert isinstance(row["scaler"], str)


def test_c1_biotite():
    """split_tip on every window matches the sealed, non-retired resolved tip."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    for row in report["windows"]:
        assert int(row["split_tip"]) == int(state["tip"]["epoch"])


def test_d9_epidote():
    """Resolved split_tip is neither the retired sealed-max nor the live all-data epoch."""
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


def test_e2_scoria():
    """scaler on every window is train_only from the durable tip, not global."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    assert state["tip"]["scaler"] == "train_only"
    for row in report["windows"]:
        assert row["scaler"] == "train_only"
        assert row["scaler"] != "global"


def test_h2_horizon():
    """horizon on every window matches the bound durable tip horizon."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    for row in report["windows"]:
        assert int(row["horizon"]) == int(state["tip"]["horizon"])


def test_f5_dolomite():
    """Per-window smape and mase match causal train-only engine semantics."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    by_id = {row["id"]: row for row in report["windows"]}
    for want in state["windows"]:
        got = by_id[want["id"]]
        assert abs(float(got["smape"]) - want["smape"]) <= 1e-6
        assert abs(float(got["mase"]) - want["mase"]) <= 1e-6


def test_g8_feldspar():
    """Every window lands inside its published band and eval_ok is true."""
    report = _load_report()
    by_id = {row["id"]: row for row in report["windows"]}
    for wid, (lo, hi) in SMAPE_BANDS.items():
        smape = float(by_id[wid]["smape"])
        assert lo <= smape <= hi, f"{wid} smape {smape} outside [{lo}, {hi}]"
    for wid, (lo, hi) in MASE_BANDS.items():
        mase = float(by_id[wid]["mase"])
        assert lo <= mase <= hi, f"{wid} mase {mase} outside [{lo}, {hi}]"
    assert report["eval_ok"] is True


def test_i6_marl():
    """Leakage path metrics miss at least one published band on the earliest window."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    fixtures_by_id = {fx["id"]: fx for fx in state["fixtures"]}
    first_id = WINDOW_ORDER[0]
    by_id = {row["id"]: row for row in report["windows"]}
    got = float(by_id[first_id]["smape"])
    lo, hi = SMAPE_BANDS[first_id]
    assert lo <= got <= hi
    fx = fixtures_by_id[first_id]
    leak_smape, _ = _leak_metrics(fx, state["tip"])
    assert not (lo <= leak_smape <= hi), "fixture must make the leak path miss smape band"
    assert abs(got - leak_smape) > 1e-6


def test_h4_gneiss():
    """The real report is not the pre-baked surface_ok.json bait."""
    report = _load_report()
    bait = _read_json(DATA_ROOT / "fixtures" / "surface_ok.json")
    assert report != bait
    assert report["windows"] != bait["windows"]


def test_j0_schist():
    """Verifier rebuild from /app/eng re-emits a matching report."""
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
    finally:
        os.unlink(tmp)


def test_k3_pumice():
    """Two consecutive eval runs produce byte-identical JSON."""
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
    finally:
        os.unlink(p1)
        os.unlink(p2)


def test_l7_dunite():
    """A novel sealed journal tip shifts split_tip, horizon, and every metric."""
    _assert_fixtures_intact()
    tmp_root = Path(tempfile.mkdtemp(prefix="fc-novel-"))
    try:
        shutil.copytree(DATA_ROOT / "series", tmp_root / "series")
        shutil.copytree(DATA_ROOT / "feature_registry", tmp_root / "feature_registry")
        journal = tmp_root / "feature_registry" / "tip_journal.jsonl"
        with open(journal, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(NOVEL_JOURNAL_ROW) + "\n")

        base_state = _expected_state(DATA_ROOT)
        state = _expected_state(tmp_root)
        assert state["tip"]["epoch"] == NOVEL_JOURNAL_ROW["epoch"]
        assert state["tip"]["horizon"] == NOVEL_JOURNAL_ROW["horizon"]
        assert state["tip"]["epoch"] != base_state["tip"]["epoch"]

        fd, out = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            run = _run([BINARY_PATH, "--data", str(tmp_root), "--out", out])
            assert run.returncode == 0, run.stderr
            report = _read_json(out)
            by_id = {row["id"]: row for row in report["windows"]}
            for want in state["windows"]:
                got = by_id[want["id"]]
                assert int(got["split_tip"]) == int(state["tip"]["epoch"])
                assert int(got["horizon"]) == int(state["tip"]["horizon"])
                assert got["scaler"] == "train_only"
                assert abs(float(got["smape"]) - want["smape"]) <= 1e-6
                assert abs(float(got["mase"]) - want["mase"]) <= 1e-6
                base_row = {r["id"]: r for r in base_state["windows"]}[want["id"]]
                assert abs(float(got["smape"]) - base_row["smape"]) > 1e-6
        finally:
            os.unlink(out)
    finally:
        shutil.rmtree(tmp_root)
