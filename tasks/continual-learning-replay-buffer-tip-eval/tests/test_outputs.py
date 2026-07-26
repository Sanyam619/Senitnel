"""Verifier tests for the continual-learning replay-buffer tip evaluation report."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

REPORT_PATH = "/output/cl-eval.json"
BINARY_PATH = "/app/eng/target/release/cl-eval"
DATA_ROOT = Path("/app/data")
CRATE_ROOT = Path("/app/eng")
SCHEMA_TAG = "cl-eval-v1"
TASK_ORDER = ("t_alpha", "t_beta", "t_gamma", "t_delta")
ACC_BANDS = {
    "t_alpha": (0.770, 0.790),
    "t_beta": (0.690, 0.710),
    "t_gamma": (0.710, 0.730),
    "t_delta": (0.772, 0.792),
}
FORG_BANDS = {
    "t_alpha": (0.010, 0.030),
    "t_beta": (0.050, 0.070),
    "t_gamma": (0.000, 0.020),
    "t_delta": (0.000, 0.010),
}
NOVEL_JOURNAL_ROW = {
    "tip": "tip_n5",
    "epoch": 10,
    "replay_frac": 0.55,
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
    text = (root / "replay" / "tip_journal.jsonl").read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _retired_tips(root: Path) -> set[str]:
    path = root / "replay" / "retired_tips.jsonl"
    if not path.is_file():
        return set()
    out = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.add(json.loads(line)["tip"])
    return out


def _ledger_rows(root: Path) -> list[dict]:
    rows = []
    text = (root / "replay" / "hold_ledger.jsonl").read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _roster_held(root: Path) -> set[str]:
    payload = _read_json(root / "replay" / "roster.json")
    return set(payload.get("held", []))


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
    return float(best["replay_frac"]), int(best["epoch"])


def _held_at(ledger: list[dict], tip_epoch: int) -> set[str]:
    latest: dict[str, tuple[int, str]] = {}
    for row in ledger:
        epoch = int(row["epoch"])
        if epoch > tip_epoch:
            continue
        prev = latest.get(row["id"])
        if prev is None or epoch >= prev[0]:
            latest[row["id"]] = (epoch, row["op"])
    return {sid for sid, (_, op) in latest.items() if op == "hold"}


def _task_fixtures(root: Path) -> list[dict]:
    rows = []
    for path in sorted((root / "tasks").glob("*.json")):
        rows.append(_read_json(path))
    rows.sort(key=lambda r: int(r["seq"]))
    return rows


def _expected_accuracy(fx: dict, frac: float, active: bool) -> float:
    if active:
        acc = fx["base"] + frac * fx["durable_hit"]
    else:
        acc = fx["base"]
    return max(0.0, min(1.0, acc))


def _expected_forgetting(acc: float, peak: float) -> float:
    return max(0.0, peak - acc)


def _overflow_accuracy(fx: dict, frac: float) -> float:
    acc = fx["base"] + frac * fx["overflow_hit"]
    return max(0.0, min(1.0, acc))


def _expected_state(root: Path) -> dict:
    frac, epoch = _resolve_tip(_journal_rows(root), _retired_tips(root))
    held = _held_at(_ledger_rows(root), epoch)
    fixtures = _task_fixtures(root)
    tasks = []
    for fx in fixtures:
        active = fx["stratum"] not in held
        acc = _expected_accuracy(fx, frac, active)
        forg = _expected_forgetting(acc, fx["peak"])
        tasks.append(
            {
                "id": fx["id"],
                "accuracy": acc,
                "forgetting": forg,
                "replay_frac": frac,
                "tip_epoch": epoch,
                "active": active,
                "stratum": fx["stratum"],
            }
        )
    return {
        "frac": frac,
        "epoch": epoch,
        "held": held,
        "tasks": tasks,
        "fixtures": fixtures,
        "roster": _roster_held(root),
    }


def _load_report() -> dict:
    _assert_fixtures_intact()
    assert Path(REPORT_PATH).is_file(), "missing /output/cl-eval.json"
    return _read_json(REPORT_PATH)


def test_a3_garnet():
    """Frozen task and replay materials under /app/data match fixtures.sha256."""
    _assert_fixtures_intact()


def test_b7_zircon():
    """Report advertises schema_tag, curriculum order, and required task fields."""
    report = _load_report()
    assert report.get("schema_tag") == SCHEMA_TAG
    assert isinstance(report.get("eval_ok"), bool)
    tasks = report.get("tasks")
    assert isinstance(tasks, list) and tasks
    ids = [row["id"] for row in tasks]
    assert ids == list(TASK_ORDER)
    for row in tasks:
        assert set(row) >= {"id", "accuracy", "forgetting", "replay_frac", "tip_epoch"}
        assert isinstance(row["id"], str)
        assert float("-inf") < float(row["accuracy"]) < float("inf")
        assert float("-inf") < float(row["forgetting"]) < float("inf")
        assert float("-inf") < float(row["replay_frac"]) < float("inf")
        assert isinstance(row["tip_epoch"], int)


def test_c1_biotite():
    """tip_epoch on every task row matches the sealed, non-retired resolved tip."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    for row in report["tasks"]:
        assert int(row["tip_epoch"]) == state["epoch"]


def test_d9_epidote():
    """Resolved tip_epoch is neither the retired sealed-max nor a live overflow epoch."""
    rows = _journal_rows(DATA_ROOT)
    retired = _retired_tips(DATA_ROOT)
    sealed_max = max(
        (row for row in rows if row.get("sealed")),
        key=lambda r: int(r["epoch"]),
    )
    assert sealed_max["tip"] in retired, "fixture must bait sealed-max with a retired tip"
    live_epochs = {int(row["epoch"]) for row in rows if row["tip"] == "tip_live"}
    state = _expected_state(DATA_ROOT)
    assert state["epoch"] != int(sealed_max["epoch"])
    assert state["epoch"] not in live_epochs


def test_e2_scoria():
    """replay_frac matches the durable journal tip, not mirror sheets or live overflow."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    assert abs(state["frac"]) > 1e-6, "resolved replay_frac must not itself be zero"
    for row in report["tasks"]:
        assert abs(float(row["replay_frac"]) - state["frac"]) <= 1e-9


def test_m2_obsidian():
    """Held strata follow the epoch ledger, not the overstated flat roster."""
    state = _expected_state(DATA_ROOT)
    assert state["held"], "fixture must hold at least one stratum at the selected tip"
    assert state["roster"] > state["held"], "roster must overstate holds vs ledger"
    by_id = {row["id"]: row for row in state["tasks"]}
    held_tasks = [tid for tid, row in by_id.items() if not row["active"]]
    active_tasks = [tid for tid, row in by_id.items() if row["active"]]
    assert held_tasks, "at least one curriculum task must sit on a held stratum"
    assert active_tasks, "at least one curriculum task must stay active"
    report = _load_report()
    for tid in held_tasks:
        fx = {f["id"]: f for f in state["fixtures"]}[tid]
        got = float({r["id"]: r for r in report["tasks"]}[tid]["accuracy"])
        assert abs(got - fx["base"]) <= 1e-6
    for tid in active_tasks:
        fx = {f["id"]: f for f in state["fixtures"]}[tid]
        want = _expected_accuracy(fx, state["frac"], True)
        got = float({r["id"]: r for r in report["tasks"]}[tid]["accuracy"])
        assert abs(got - want) <= 1e-6


def test_f5_dolomite():
    """Per-task accuracy and forgetting match durable-hit + hold-window semantics."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    by_id = {row["id"]: row for row in report["tasks"]}
    for want in state["tasks"]:
        got = by_id[want["id"]]
        assert abs(float(got["accuracy"]) - want["accuracy"]) <= 1e-6
        assert abs(float(got["forgetting"]) - want["forgetting"]) <= 1e-6


def test_g8_feldspar():
    """Every task lands inside its published band and eval_ok is true."""
    report = _load_report()
    by_id = {row["id"]: row for row in report["tasks"]}
    for task_id, (lo, hi) in ACC_BANDS.items():
        acc = float(by_id[task_id]["accuracy"])
        assert lo <= acc <= hi, f"{task_id} accuracy {acc} outside [{lo}, {hi}]"
    for task_id, (lo, hi) in FORG_BANDS.items():
        forg = float(by_id[task_id]["forgetting"])
        assert lo <= forg <= hi, f"{task_id} forgetting {forg} outside [{lo}, {hi}]"
    assert report["eval_ok"] is True


def test_h4_gneiss():
    """The real report is not the pre-baked surface_ok.json bait."""
    report = _load_report()
    bait = _read_json(DATA_ROOT / "fixtures" / "surface_ok.json")
    assert report != bait
    assert report["tasks"] != bait["tasks"]


def test_i6_marl():
    """The earliest task stays in band and is not the overflow-path value."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    fixtures_by_id = {fx["id"]: fx for fx in state["fixtures"]}
    first_id = TASK_ORDER[0]
    by_id = {row["id"]: row for row in report["tasks"]}
    got = float(by_id[first_id]["accuracy"])
    lo, hi = ACC_BANDS[first_id]
    assert lo <= got <= hi
    fx = fixtures_by_id[first_id]
    overflow_acc = _overflow_accuracy(fx, state["frac"])
    assert not (lo <= overflow_acc <= hi), "fixture must make the overflow path miss band"
    assert abs(got - overflow_acc) > 1e-6


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
    """A novel sealed tip shifts tip_epoch, replay_frac, holds, and every accuracy."""
    _assert_fixtures_intact()
    tmp_root = Path(tempfile.mkdtemp(prefix="cl-novel-"))
    try:
        shutil.copytree(DATA_ROOT / "tasks", tmp_root / "tasks")
        shutil.copytree(DATA_ROOT / "replay", tmp_root / "replay")
        journal = tmp_root / "replay" / "tip_journal.jsonl"
        with open(journal, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(NOVEL_JOURNAL_ROW) + "\n")

        base_state = _expected_state(DATA_ROOT)
        state = _expected_state(tmp_root)
        assert state["epoch"] == NOVEL_JOURNAL_ROW["epoch"]
        assert abs(state["frac"] - NOVEL_JOURNAL_ROW["replay_frac"]) <= 1e-9
        assert state["epoch"] != base_state["epoch"]
        assert abs(state["frac"] - base_state["frac"]) > 1e-6
        assert state["held"] != base_state["held"], "novel tip must move the hold window"

        fd, out = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            run = _run([BINARY_PATH, "--data", str(tmp_root), "--out", out])
            assert run.returncode == 0, run.stderr
            report = _read_json(out)
            by_id = {row["id"]: row for row in report["tasks"]}
            for want in state["tasks"]:
                got = by_id[want["id"]]
                assert int(got["tip_epoch"]) == state["epoch"]
                assert abs(float(got["replay_frac"]) - state["frac"]) <= 1e-9
                assert abs(float(got["accuracy"]) - want["accuracy"]) <= 1e-6
                assert abs(float(got["forgetting"]) - want["forgetting"]) <= 1e-6
                base_row = {r["id"]: r for r in base_state["tasks"]}[want["id"]]
                assert abs(float(got["accuracy"]) - base_row["accuracy"]) > 1e-6
        finally:
            os.unlink(out)
    finally:
        shutil.rmtree(tmp_root)
