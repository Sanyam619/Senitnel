"""Verifier tests for the preference-model KL-constrained evaluation report."""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

REPORT_PATH = "/output/pref-eval.json"
BINARY_PATH = "/app/eng/target/release/pref-eval"
DATA_ROOT = Path("/app/data")
CRATE_ROOT = Path("/app/eng")
SCHEMA_TAG = "pref-eval-v1"
SLICE_IDS = ("s_alpha", "s_beta", "s_gamma", "s_delta")
BANDS = {
    "s_alpha": (0.68, 0.76),
    "s_beta": (0.60, 0.70),
    "s_gamma": (0.74, 0.82),
    "s_delta": (0.66, 0.74),
}
KL_CEIL = {
    "s_alpha": 0.12,
    "s_beta": 0.15,
    "s_gamma": 0.10,
    "s_delta": 0.14,
}
NOVEL_JOURNAL_ROW = {
    "tip": "tip_n8",
    "epoch": 8,
    "beta": 0.35,
    "sealed": True,
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
    text = (root / "tips" / "tip_journal.jsonl").read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _retired_tips(root: Path) -> set[str]:
    path = root / "tips" / "retired_tips.jsonl"
    if not path.is_file():
        return set()
    out = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.add(json.loads(line)["tip"])
    return out


def _resolve_tip(rows: list[dict], retired: set[str]) -> tuple[float, int]:
    best = None
    for row in rows:
        if not row.get("sealed"):
            continue
        if row.get("tip") in retired:
            continue
        if best is None or int(row["epoch"]) >= int(best["epoch"]):
            best = row
    assert best is not None, "journal has no selectable sealed tip"
    return float(best["beta"]), int(best["epoch"])


def _sigmoid(x: float) -> float:
    if x >= 0.0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def _soft_win(margins: list[float], beta: float) -> float:
    scale = beta if abs(beta) >= 1e-12 else 1e-12
    return sum(_sigmoid(scale * m) for m in margins) / len(margins)


def _kl_row(pc: list[float], pr: list[float]) -> float:
    s = 0.0
    for a, b in zip(pc, pr):
        a = max(a, 1e-15)
        b = max(b, 1e-15)
        s += a * math.log(a / b)
    return s


def _mean_kl(cands: list[list[float]], refs: list[list[float]]) -> float:
    n = min(len(cands), len(refs))
    assert n > 0
    return sum(_kl_row(cands[i], refs[i]) for i in range(n)) / n


def _load_margins(root: Path, sid: str) -> list[float]:
    payload = _read_json(root / "prefs" / f"{sid}.json")
    return [float(p["m"]) for p in payload["pairs"]]


def _load_probs(root: Path, kind: str, sid: str) -> list[list[float]]:
    payload = _read_json(root / kind / f"{sid}.json")
    return [[float(x) for x in row] for row in payload["probs"]]


def _expected_state(root: Path) -> dict:
    beta, tip_epoch = _resolve_tip(_journal_rows(root), _retired_tips(root))
    slices = {}
    for sid in SLICE_IDS:
        pref_path = root / "prefs" / f"{sid}.json"
        if not pref_path.is_file():
            continue
        margins = _load_margins(root, sid)
        cand = _load_probs(root, "policy", sid)
        ref = _load_probs(root, "ref", sid)
        slices[sid] = {
            "win_rate": _soft_win(margins, beta),
            "kl_to_ref": _mean_kl(cand, ref),
            "beta": beta,
            "tip_epoch": tip_epoch,
        }
    return {"beta": beta, "tip_epoch": tip_epoch, "slices": slices}


def _load_report() -> dict:
    _assert_fixtures_intact()
    assert Path(REPORT_PATH).is_file(), "missing /output/pref-eval.json"
    return _read_json(REPORT_PATH)


def _slice_map(report: dict) -> dict[str, dict]:
    return {row["id"]: row for row in report["slices"]}


def test_g6_shale():
    """Frozen materials under /app/data match fixtures.sha256."""
    _assert_fixtures_intact()


def test_n4_quartz():
    """Report advertises schema_tag and required slice fields."""
    report = _load_report()
    assert report.get("schema_tag") == SCHEMA_TAG
    assert isinstance(report.get("eval_ok"), bool)
    slices = report.get("slices")
    assert isinstance(slices, list) and slices
    ids = {row["id"] for row in slices}
    assert ids == set(SLICE_IDS)
    for row in slices:
        assert set(row) >= {"id", "win_rate", "kl_to_ref", "beta", "tip_epoch"}
        assert isinstance(row["id"], str)
        assert float("-inf") < float(row["win_rate"]) < float("inf")
        assert float("-inf") < float(row["kl_to_ref"]) < float("inf")
        assert float("-inf") < float(row["beta"]) < float("inf")
        assert isinstance(row["tip_epoch"], int)


def test_m9_jade():
    """tip_epoch and beta match sealed durable tip, not live/retired baits."""
    report = _load_report()
    exp = _expected_state(DATA_ROOT)
    live_beta = None
    for line in (DATA_ROOT / "tips" / "live.toml").read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("beta"):
            live_beta = float(line.split("=", 1)[1].strip())
    assert live_beta is not None
    for row in report["slices"]:
        assert int(row["tip_epoch"]) == int(exp["tip_epoch"])
        assert abs(float(row["beta"]) - float(exp["beta"])) < 1e-9
        assert int(row["tip_epoch"]) != 5
        assert int(row["tip_epoch"]) != 7
        assert abs(float(row["beta"]) - live_beta) > 1e-6
        assert abs(float(row["beta"]) - 0.05) > 1e-6


def test_r6_onyx():
    """Every graded slice lands inside published win-rate bands."""
    report = _load_report()
    for row in report["slices"]:
        lo, hi = BANDS[row["id"]]
        win = float(row["win_rate"])
        assert lo <= win <= hi, f"{row['id']} win_rate {win} outside [{lo}, {hi}]"


def test_k2_topaz():
    """kl_to_ref stays at or under each published ceiling and is non-trivial."""
    report = _load_report()
    exp = _expected_state(DATA_ROOT)
    sm = _slice_map(report)
    for sid in SLICE_IDS:
        kl = float(sm[sid]["kl_to_ref"])
        assert kl <= KL_CEIL[sid] + 1e-9, f"{sid} kl {kl} exceeds ceiling"
        assert kl > 1e-4, f"{sid} kl looks trivially zero"
        assert abs(kl - exp["slices"][sid]["kl_to_ref"]) < 1e-6


def test_p3_flint():
    """win_rate matches soft pairwise wins under seated beta (not hard 1.0)."""
    report = _load_report()
    exp = _expected_state(DATA_ROOT)
    sm = _slice_map(report)
    for sid in SLICE_IDS:
        got = float(sm[sid]["win_rate"])
        want = exp["slices"][sid]["win_rate"]
        assert abs(got - want) < 1e-6, f"{sid} win {got} != {want}"
        assert got < 0.999, f"{sid} looks like always-win polarity"


def test_c8_coral():
    """eval_ok is true and tip fields are consistent across slices."""
    report = _load_report()
    assert report["eval_ok"] is True
    betas = {float(row["beta"]) for row in report["slices"]}
    epochs = {int(row["tip_epoch"]) for row in report["slices"]}
    assert len(betas) == 1
    assert len(epochs) == 1


def test_v5_mica():
    """Surface prefprobe can look healthy while deep KL seating is required."""
    report = _load_report()
    proc = _run(["bash", "/app/tools/prefprobe", str(DATA_ROOT)])
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "healthy: yes" in out
    assert report["eval_ok"] is True
    # Probe hard-win mean is not the graded soft win_rate vector.
    sm = _slice_map(report)
    assert any(abs(float(sm[sid]["win_rate"]) - 1.0) > 1e-3 for sid in SLICE_IDS)


def test_w7_beryl():
    """Published numbers are not a copy of the captured surface_ok sweep."""
    report = _load_report()
    sweep = _read_json(DATA_ROOT / "fixtures" / "surface_ok.json")
    sm = _slice_map(report)
    sw = {row["id"]: row for row in sweep["slices"]}
    for sid in SLICE_IDS:
        assert abs(float(sm[sid]["win_rate"]) - float(sw[sid]["win_rate"])) > 1e-3
        assert abs(float(sm[sid]["beta"]) - float(sw[sid]["beta"])) > 1e-3
        assert int(sm[sid]["tip_epoch"]) != int(sw[sid]["tip_epoch"])


def test_h1_slate():
    """Verifier rebuild from /app/eng then re-emit matches the agent report."""
    report = Path(REPORT_PATH).read_bytes()
    build = _run(
        ["cargo", "build", "--release", "--offline", "--locked"],
        cwd=str(CRATE_ROOT),
    )
    assert build.returncode == 0, build.stderr
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "pref-eval.json"
        run = _run([BINARY_PATH, "--data", str(DATA_ROOT), "--out", str(out)])
        assert run.returncode == 0, run.stderr
        assert out.read_bytes() == report


def test_u4_basalt():
    """Two consecutive entrypoint runs publish byte-identical reports."""
    with tempfile.TemporaryDirectory() as tmp:
        a = Path(tmp) / "a.json"
        b = Path(tmp) / "b.json"
        for path in (a, b):
            env = os.environ.copy()
            env["PREF_REPORT_OUT"] = str(path)
            run = _run(["bash", "/app/scripts/run_pref_eval.sh"], env=env)
            assert run.returncode == 0, run.stderr
        assert a.read_bytes() == b.read_bytes()


def test_y2_chert():
    """Novel preference margins move win_rate away from the shipped seating."""
    exp0 = _expected_state(DATA_ROOT)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "data"
        shutil.copytree(DATA_ROOT, root)
        sid = "s_alpha"
        pref = _read_json(root / "prefs" / f"{sid}.json")
        for pair in pref["pairs"]:
            pair["m"] = float(pair["m"]) * 0.15
        (root / "prefs" / f"{sid}.json").write_text(
            json.dumps(pref, indent=2) + "\n", encoding="utf-8"
        )
        exp1 = _expected_state(root)
        assert abs(exp1["slices"][sid]["win_rate"] - exp0["slices"][sid]["win_rate"]) > 0.02
        out = Path(tmp) / "novel.json"
        run = _run([BINARY_PATH, "--data", str(root), "--out", str(out)])
        assert run.returncode == 0, run.stderr
        report = _read_json(out)
        sm = _slice_map(report)
        assert abs(float(sm[sid]["win_rate"]) - exp1["slices"][sid]["win_rate"]) < 1e-6


def test_j3_pyrite():
    """Novel sealed journal tip moves beta/tip_epoch and soft win rates."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "data"
        shutil.copytree(DATA_ROOT, root)
        with (root / "tips" / "tip_journal.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(NOVEL_JOURNAL_ROW) + "\n")
        exp = _expected_state(root)
        assert int(exp["tip_epoch"]) == 8
        assert abs(float(exp["beta"]) - 0.35) < 1e-9
        out = Path(tmp) / "novel-tip.json"
        run = _run([BINARY_PATH, "--data", str(root), "--out", str(out)])
        assert run.returncode == 0, run.stderr
        report = _read_json(out)
        sm = _slice_map(report)
        for sid in SLICE_IDS:
            assert int(sm[sid]["tip_epoch"]) == 8
            assert abs(float(sm[sid]["beta"]) - 0.35) < 1e-9
            assert abs(float(sm[sid]["win_rate"]) - exp["slices"][sid]["win_rate"]) < 1e-6
        # Novel tip beta is outside shipped bands for at least one slice.
        assert any(
            not (BANDS[sid][0] <= float(sm[sid]["win_rate"]) <= BANDS[sid][1])
            for sid in SLICE_IDS
        )
