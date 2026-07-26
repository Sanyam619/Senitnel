"""Verifier tests for the MoE router load-balance evaluation report."""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

REPORT_PATH = "/output/moe-eval.json"
BINARY_PATH = "/app/eng/target/release/moe-eval"
DATA_ROOT = Path("/app/data")
CRATE_ROOT = Path("/app/eng")
SCHEMA_TAG = "moe-eval-v1"
SLICE_IDS = ("s_alpha", "s_beta", "s_gamma", "s_delta")
BANDS = {
    "s_alpha": (2.693562, 2.860174),
    "s_beta": (1.853196, 1.967826),
    "s_gamma": (2.091763, 2.221150),
    "s_delta": (2.602896, 2.763900),
}
NOVEL_LOGITS = [1.4, 0.7, 2.1, 0.5, 1.6]
NOVEL_JOURNAL_ROW = {
    "tip": "tip_n8",
    "epoch": 8,
    "tip_temp": 0.6,
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


def _read_tip_temp(path: Path) -> float:
    tip = 1.0
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("tip_temp"):
            tip = float(line.split("=", 1)[1].strip())
    return tip


def _journal_rows(root: Path) -> list[dict]:
    rows = []
    text = (root / "routers" / "tip_journal.jsonl").read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _retired_tips(root: Path) -> set[str]:
    path = root / "routers" / "retired_tips.jsonl"
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
    return float(best["tip_temp"]), int(best["epoch"])


def _ledger_rows(root: Path) -> list[dict]:
    rows = []
    text = (root / "routers" / "hold_ledger.jsonl").read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _held_at(ledger: list[dict], tip_epoch: int) -> set[str]:
    latest: dict[str, tuple[int, str]] = {}
    for row in ledger:
        epoch = int(row["epoch"])
        if epoch > tip_epoch:
            continue
        prev = latest.get(row["id"])
        if prev is None or epoch >= prev[0]:
            latest[row["id"]] = (epoch, row["op"])
    return {eid for eid, (_, op) in latest.items() if op == "hold"}


def _expert_ids(root: Path) -> list[str]:
    return sorted(p.stem for p in (root / "experts").glob("*.json"))


def _caps(root: Path, ids: list[str]) -> list[float]:
    out = []
    for eid in ids:
        payload = _read_json(root / "experts" / f"{eid}.json")
        out.append(float(payload.get("capacity", 1.0)))
    return out


def _seat(
    logits: list[float], ids: list[str], caps: list[float], held: set[str], temp: float
) -> list[float]:
    scaled = [v / temp for v in logits]
    mx = max(scaled)
    ex = [math.exp(v - mx) for v in scaled]
    total = sum(ex)
    probs = [e / total for e in ex]
    weighted = [
        caps[i] * probs[i] if ids[i] not in held else 0.0 for i in range(len(ids))
    ]
    mass = sum(weighted)
    return [w / mass for w in weighted]


def _entropy(weights: list[float]) -> float:
    return -sum(w * math.log(w) for w in weights if w > 1e-15)


def _slice_logits(root: Path) -> dict[str, list[float]]:
    out = {}
    for path in sorted((root / "eval").glob("*.json")):
        payload = _read_json(path)
        out[payload["id"]] = [float(v) for v in payload["logits"]]
    return out


def _expected_state(root: Path) -> dict:
    tip_temp, tip_epoch = _resolve_tip(_journal_rows(root), _retired_tips(root))
    held = _held_at(_ledger_rows(root), tip_epoch)
    ids = _expert_ids(root)
    caps = _caps(root, ids)
    slices = _slice_logits(root)
    seated = {sid: _seat(row, ids, caps, held, tip_temp) for sid, row in slices.items()}
    loads = [
        sum(w[i] for w in seated.values()) / len(seated) for i in range(len(ids))
    ]
    return {
        "tip_temp": tip_temp,
        "tip_epoch": tip_epoch,
        "held": held,
        "ids": ids,
        "caps": caps,
        "seated": seated,
        "loads": loads,
    }


def _load_report() -> dict:
    _assert_fixtures_intact()
    assert Path(REPORT_PATH).is_file(), "missing /output/moe-eval.json"
    return _read_json(REPORT_PATH)


def test_g6_shale():
    """Frozen materials under /app/data match fixtures.sha256."""
    _assert_fixtures_intact()


def test_n4_quartz():
    """Report advertises schema_tag and required expert/slice fields."""
    report = _load_report()
    assert report.get("schema_tag") == SCHEMA_TAG
    assert isinstance(report.get("eval_ok"), bool)
    experts = report.get("experts")
    slices = report.get("slices")
    assert isinstance(experts, list) and experts
    assert isinstance(slices, list) and slices
    for row in experts:
        assert set(row) >= {"id", "load_share", "active"}
        assert isinstance(row["id"], str)
        assert float("-inf") < float(row["load_share"]) < float("inf")
        assert isinstance(row["active"], bool)
    ids = {row["id"] for row in slices}
    assert ids == set(SLICE_IDS)
    for row in slices:
        assert set(row) >= {"id", "perplexity", "expert_entropy", "router_temp"}
        assert float("-inf") < float(row["perplexity"]) < float("inf")
        assert float("-inf") < float(row["expert_entropy"]) < float("inf")
        assert float("-inf") < float(row["router_temp"]) < float("inf")


def test_w7_beryl():
    """Active load shares close to unit mass; inactive shares are zero."""
    report = _load_report()
    active_sum = 0.0
    for row in report["experts"]:
        share = float(row["load_share"])
        if row["active"]:
            active_sum += share
        else:
            assert abs(share) <= 1e-9
    assert abs(active_sum - 1.0) <= 1e-6


def test_k2_topaz():
    """Holds resolve from the epoch ledger, not the flat roster summary."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    by_id = {row["id"]: row for row in report["experts"]}
    assert state["held"]
    for hid in state["held"]:
        assert hid in by_id
        assert by_id[hid]["active"] is False
        assert abs(float(by_id[hid]["load_share"])) <= 1e-9
    roster = set(_read_json(DATA_ROOT / "routers" / "hold.json").get("held", []))
    bait_only = roster - state["held"]
    assert bait_only, "fixture roster must overstate the resolved held set"
    for eid in bait_only:
        assert by_id[eid]["active"] is True
        assert float(by_id[eid]["load_share"]) > 1e-6


def test_m9_jade():
    """Every slice router_temp matches the selected durable tip, not mirrors or retired tips."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    live = _read_tip_temp(DATA_ROOT / "routers" / "live.toml")
    mirror = _read_tip_temp(DATA_ROOT / "routers" / "durable.toml")
    rows = _journal_rows(DATA_ROOT)
    retired = _retired_tips(DATA_ROOT)
    sealed_max = max(
        (row for row in rows if row.get("sealed")),
        key=lambda r: int(r["epoch"]),
    )
    assert sealed_max["tip"] in retired, "fixture must bait sealed-max with a retired tip"
    assert abs(state["tip_temp"] - float(sealed_max["tip_temp"])) > 1e-6
    assert abs(state["tip_temp"] - live) > 1e-6
    assert abs(state["tip_temp"] - mirror) > 1e-6
    for row in report["slices"]:
        assert abs(float(row["router_temp"]) - state["tip_temp"]) <= 1e-9


def test_r6_onyx():
    """Each graded slice perplexity lands inside the documented band."""
    report = _load_report()
    by_id = {row["id"]: row for row in report["slices"]}
    for sid, (lo, hi) in BANDS.items():
        ppl = float(by_id[sid]["perplexity"])
        assert lo <= ppl <= hi, f"{sid} perplexity {ppl} outside [{lo}, {hi}]"


def test_p3_flint():
    """expert_entropy matches the seated post-hold distribution, not uniform bait."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    by_id = {row["id"]: row for row in report["slices"]}
    active_n = len(state["ids"]) - len(state["held"])
    uniform = math.log(active_n)
    for sid, weights in state["seated"].items():
        want = _entropy(weights)
        got = float(by_id[sid]["expert_entropy"])
        assert abs(got - want) <= 1e-6
        assert abs(got - uniform) > 1e-3


def test_c8_coral():
    """eval_ok is true under deep invariants, not a uniform-share heuristic."""
    report = _load_report()
    assert report["eval_ok"] is True
    shares = [float(e["load_share"]) for e in report["experts"]]
    assert max(shares) - min(shares) > 0.02


def test_v5_mica():
    """Deep seating matches capacity-weighted hold-aware loads; moeprobe is bait."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    by_id = {row["id"]: row for row in report["experts"]}
    for i, eid in enumerate(state["ids"]):
        assert abs(float(by_id[eid]["load_share"]) - state["loads"][i]) <= 1e-6
        assert by_id[eid]["active"] is (eid not in state["held"])
    proc = _run(["/app/tools/moeprobe", REPORT_PATH])
    assert proc.returncode == 0
    assert "balanced: yes" not in proc.stdout


def test_h1_slate():
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


def test_u4_basalt():
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


def test_y2_chert():
    """A verifier-owned novel slice scores under independently computed metrics."""
    _assert_fixtures_intact()
    tmp_root = Path(tempfile.mkdtemp(prefix="moe-novel-"))
    try:
        shutil.copytree(DATA_ROOT / "experts", tmp_root / "experts")
        shutil.copytree(DATA_ROOT / "routers", tmp_root / "routers")
        shutil.copytree(DATA_ROOT / "eval", tmp_root / "eval")
        novel_path = tmp_root / "eval" / "s_novel.json"
        novel_path.write_text(
            json.dumps({"id": "s_novel", "logits": NOVEL_LOGITS}, indent=2) + "\n",
            encoding="utf-8",
        )
        state = _expected_state(tmp_root)
        want = state["seated"]["s_novel"]
        want_ent = _entropy(want)
        fd, out = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            run = _run([BINARY_PATH, "--data", str(tmp_root), "--out", out])
            assert run.returncode == 0, run.stderr
            report = _read_json(out)
            by_id = {row["id"]: row for row in report["slices"]}
            assert "s_novel" in by_id
            got_ppl = float(by_id["s_novel"]["perplexity"])
            assert abs(got_ppl - math.exp(want_ent)) <= 1e-6
            assert abs(float(by_id["s_novel"]["router_temp"]) - state["tip_temp"]) <= 1e-9
            assert abs(float(by_id["s_novel"]["expert_entropy"]) - want_ent) <= 1e-6
        finally:
            os.unlink(out)
    finally:
        shutil.rmtree(tmp_root)


def test_j3_pyrite():
    """A novel sealed journal tip shifts temperature and the hold window together."""
    _assert_fixtures_intact()
    tmp_root = Path(tempfile.mkdtemp(prefix="moe-journal-"))
    try:
        shutil.copytree(DATA_ROOT / "experts", tmp_root / "experts")
        shutil.copytree(DATA_ROOT / "routers", tmp_root / "routers")
        shutil.copytree(DATA_ROOT / "eval", tmp_root / "eval")
        journal = tmp_root / "routers" / "tip_journal.jsonl"
        with open(journal, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(NOVEL_JOURNAL_ROW) + "\n")

        base = _expected_state(DATA_ROOT)
        state = _expected_state(tmp_root)
        assert state["tip_epoch"] == NOVEL_JOURNAL_ROW["epoch"]
        assert state["held"] != base["held"], "novel tip must move the hold window"

        fd, out = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            run = _run([BINARY_PATH, "--data", str(tmp_root), "--out", out])
            assert run.returncode == 0, run.stderr
            report = _read_json(out)
            slice_by_id = {row["id"]: row for row in report["slices"]}
            for sid, weights in state["seated"].items():
                want_ent = _entropy(weights)
                row = slice_by_id[sid]
                assert abs(float(row["router_temp"]) - state["tip_temp"]) <= 1e-9
                assert abs(float(row["expert_entropy"]) - want_ent) <= 1e-6
            expert_by_id = {row["id"]: row for row in report["experts"]}
            active_sum = 0.0
            for i, eid in enumerate(state["ids"]):
                row = expert_by_id[eid]
                assert row["active"] is (eid not in state["held"])
                assert abs(float(row["load_share"]) - state["loads"][i]) <= 1e-6
                if row["active"]:
                    active_sum += float(row["load_share"])
            assert abs(active_sum - 1.0) <= 1e-6
        finally:
            os.unlink(out)
    finally:
        shutil.rmtree(tmp_root)
