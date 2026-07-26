"""Verifier tests for the mixture-of-depths token-routing evaluation report."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

REPORT_PATH = "/output/mod-eval.json"
BINARY_PATH = "/app/eng/target/release/mod-eval"
DATA_ROOT = Path("/app/data")
CRATE_ROOT = Path("/app/eng")
TESTS_DIR = Path("/tests")
TESTS_HOLD = Path("/tmp/mod_verifier_hold/tests")
SCHEMA_TAG = "mod-eval-v1"
REQUIRED_IDS = ("cold_a", "resume_a", "cold_b", "resume_b", "mix_c", "mix_d")
DEPTH_BAND = (4.35, 4.65)
PPL_BANDS = {
    "cold_a": (4.155, 4.325),
    "resume_a": (4.155, 4.325),
    "cold_b": (5.075, 5.282),
    "resume_b": (5.075, 5.282),
    "mix_c": (3.648, 3.798),
    "mix_d": (4.732, 4.925),
}
NOVEL_JOURNAL_ROW = {
    "tip": "tip_n8",
    "epoch": 8,
    "capacity": 0.6,
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


def _finite(v: float) -> bool:
    return float("-inf") < v < float("inf")


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


def _schedule(root: Path, cap: float, mirror: bool = False) -> tuple[float, float]:
    name = "schedule_mirror.json" if mirror else "depth_schedule.json"
    base = root / "ledger" if mirror else root / "routers"
    payload = _read_json(base / name)
    key = f"{cap:.2f}"
    entry = payload[key]
    return float(entry["shallow"]), float(entry["deep"])


def _avg_depth(scores: list[float], cap: float, shallow: float, deep: float) -> float:
    n = len(scores)
    k = round(n * cap)
    k = max(0, min(n, k))
    order = sorted(range(n), key=lambda i: scores[i], reverse=True)
    depths = [shallow] * n
    for i in order[:k]:
        depths[i] = deep
    return sum(depths) / n


def _perplexity(base_nll: float, cap: float) -> float:
    return (2.718281828459045 ** base_nll) / (1.0 + cap)


def _scenarios(root: Path) -> dict[str, dict]:
    out = {}
    for path in sorted((root / "eval").glob("*.json")):
        payload = _read_json(path)
        out[payload["id"]] = payload
    return out


def _expected_state(root: Path) -> dict:
    tip = _resolve_tip(_journal_rows(root), _retired_tips(root))
    cap = float(tip["capacity"])
    epoch = int(tip["epoch"])
    shallow, deep = _schedule(root, cap, mirror=False)
    rows = {}
    for sid, sc in _scenarios(root).items():
        scores = [float(v) for v in sc["token_scores"]]
        rows[sid] = {
            "id": sid,
            "perplexity": _perplexity(float(sc["base_nll"]), cap),
            "avg_depth": _avg_depth(scores, cap, shallow, deep),
            "capacity": cap,
            "tip_epoch": epoch,
        }
    return {"tip": tip, "capacity": cap, "epoch": epoch, "rows": rows}


def _load_report() -> dict:
    assert Path(REPORT_PATH).is_file(), f"missing report at {REPORT_PATH}"
    return _read_json(REPORT_PATH)


def _scenario_map(report: dict) -> dict[str, dict]:
    return {row["id"]: row for row in report["scenarios"]}


def _seal_tests() -> None:
    """Move /tests children aside so the graded binary cannot import EXPECTED."""
    if not TESTS_DIR.is_dir():
        return
    if TESTS_HOLD.exists():
        shutil.rmtree(TESTS_HOLD)
    TESTS_HOLD.mkdir(parents=True, exist_ok=True)
    for child in list(TESTS_DIR.iterdir()):
        dest = TESTS_HOLD / child.name
        if dest.exists():
            if dest.is_dir():
                shutil.rmtree(dest)
            else:
                dest.unlink()
        child.rename(dest)


def _unseal_tests() -> None:
    """Restore /tests after a sealed binary pass so pytest can finish."""
    if not TESTS_HOLD.is_dir():
        return
    TESTS_DIR.mkdir(parents=True, exist_ok=True)
    for child in list(TESTS_HOLD.iterdir()):
        dest = TESTS_DIR / child.name
        if dest.exists():
            if dest.is_dir():
                shutil.rmtree(dest)
            else:
                dest.unlink()
        child.rename(dest)
    try:
        TESTS_HOLD.rmdir()
    except OSError:
        shutil.rmtree(TESTS_HOLD, ignore_errors=True)


def _rebuild() -> None:
    proc = _run(
        ["cargo", "build", "--release", "--offline", "--locked"],
        cwd=str(CRATE_ROOT),
    )
    assert proc.returncode == 0, proc.stderr


def _run_binary(data_root: Path, out_path: Path) -> dict:
    _seal_tests()
    try:
        proc = _run(
            [BINARY_PATH, "--data", str(data_root), "--out", str(out_path)],
        )
        assert proc.returncode == 0, proc.stderr
        return _read_json(out_path)
    finally:
        _unseal_tests()


def test_a3_garnet():
    """Fixture digests under /app/data remain intact."""
    _assert_fixtures_intact()


def test_b7_zircon():
    """Report schema, required ids, and field types hold."""
    report = _load_report()
    assert report["schema_tag"] == SCHEMA_TAG
    assert isinstance(report["bands_ok"], bool)
    ids = [row["id"] for row in report["scenarios"]]
    assert set(ids) == set(REQUIRED_IDS)
    assert len(ids) == len(REQUIRED_IDS)
    for row in report["scenarios"]:
        assert isinstance(row["id"], str)
        assert isinstance(row["perplexity"], (int, float)) and _finite(float(row["perplexity"]))
        assert isinstance(row["avg_depth"], (int, float)) and _finite(float(row["avg_depth"]))
        assert isinstance(row["capacity"], (int, float)) and _finite(float(row["capacity"]))
        assert isinstance(row["tip_epoch"], int)


def test_c1_biotite():
    """tip_epoch equals the registry-resolved durable tip epoch."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    for row in report["scenarios"]:
        assert int(row["tip_epoch"]) == state["epoch"]


def test_d9_epidote():
    """capacity equals durable tip capacity, not live full-depth or retired."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    live = float(
        next(
            line.split("=", 1)[1].strip()
            for line in (DATA_ROOT / "routers" / "live.toml")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip().startswith("capacity")
        )
    )
    retired_caps = {
        float(r["capacity"])
        for r in _journal_rows(DATA_ROOT)
        if r["tip"] in _retired_tips(DATA_ROOT)
    }
    for row in report["scenarios"]:
        cap = float(row["capacity"])
        assert abs(cap - state["capacity"]) < 1e-12
        assert abs(cap - live) > 1e-9
        assert all(abs(cap - rc) > 1e-9 for rc in retired_caps)
    for row in report["scenarios"]:
        lo, hi = DEPTH_BAND
        assert lo <= float(row["avg_depth"]) <= hi


def test_e2_scoria():
    """avg_depth lands in the documented band for every scenario."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    smap = _scenario_map(report)
    lo, hi = DEPTH_BAND
    for sid in REQUIRED_IDS:
        depth = float(smap[sid]["avg_depth"])
        assert lo <= depth <= hi
        assert abs(depth - state["rows"][sid]["avg_depth"]) < 1e-9


def test_f5_dolomite():
    """Cold/resume perplexity partners agree within 1e-4."""
    report = _load_report()
    smap = _scenario_map(report)
    assert abs(float(smap["cold_a"]["perplexity"]) - float(smap["resume_a"]["perplexity"])) < 1e-4
    assert abs(float(smap["cold_b"]["perplexity"]) - float(smap["resume_b"]["perplexity"])) < 1e-4


def test_g8_feldspar():
    """Perplexity bands hold and bands_ok is true."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    smap = _scenario_map(report)
    assert report["bands_ok"] is True
    for sid in REQUIRED_IDS:
        ppl = float(smap[sid]["perplexity"])
        lo, hi = PPL_BANDS[sid]
        assert lo <= ppl <= hi
        assert abs(ppl - state["rows"][sid]["perplexity"]) < 1e-9


def test_i6_marl():
    """Live full-depth capacity path sits outside avg-depth / capacity outcomes."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    live = 1.0
    shallow, deep = _schedule(DATA_ROOT, live, mirror=False)
    for sid, sc in _scenarios(DATA_ROOT).items():
        scores = [float(v) for v in sc["token_scores"]]
        full_depth = _avg_depth(scores, live, shallow, deep)
        row = _scenario_map(report)[sid]
        assert abs(float(row["capacity"]) - live) > 1e-9
        assert abs(float(row["avg_depth"]) - full_depth) > 1e-6
        assert abs(float(row["avg_depth"]) - state["rows"][sid]["avg_depth"]) < 1e-9


def test_h4_gneiss():
    """Published report is not the surface_ok bait and still clears bands."""
    report = _load_report()
    bait = _read_json(DATA_ROOT / "fixtures" / "surface_ok.json")
    assert report != bait
    assert bait.get("bands_ok") is True
    lo, hi = DEPTH_BAND
    for row in report["scenarios"]:
        assert lo <= float(row["avg_depth"]) <= hi


def test_j0_schist():
    """Rebuild from /app/eng and re-run matches the published report."""
    report = _load_report()
    _rebuild()
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "mod-eval.json"
        again = _run_binary(DATA_ROOT, out)
    assert again == report


def test_k3_pumice():
    """Two consecutive runs are byte-identical and band-clean."""
    report = _load_report()
    with tempfile.TemporaryDirectory() as tmp:
        out1 = Path(tmp) / "a.json"
        out2 = Path(tmp) / "b.json"
        r1 = _run_binary(DATA_ROOT, out1)
        r2 = _run_binary(DATA_ROOT, out2)
        b1 = out1.read_bytes()
        b2 = out2.read_bytes()
    assert r1 == r2
    assert b1 == b2
    assert r1 == report


def test_l7_dunite():
    """A novel sealed tip moves tip_epoch, capacity, and avg_depth."""
    base = _expected_state(DATA_ROOT)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp) / "data"
        shutil.copytree(DATA_ROOT / "routers", tmp_root / "routers")
        shutil.copytree(DATA_ROOT / "eval", tmp_root / "eval")
        shutil.copytree(DATA_ROOT / "ckpt", tmp_root / "ckpt")
        shutil.copytree(DATA_ROOT / "ledger", tmp_root / "ledger")
        journal = tmp_root / "routers" / "tip_journal.jsonl"
        with journal.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(NOVEL_JOURNAL_ROW, separators=(",", ":")) + "\n")
        state = _expected_state(tmp_root)
        assert state["epoch"] != base["epoch"]
        assert abs(state["capacity"] - base["capacity"]) > 1e-9
        out = Path(tmp) / "novel.json"
        got = _run_binary(tmp_root, out)
        smap = _scenario_map(got)
        lo, hi = DEPTH_BAND
        # Novel tip capacity keys a deeper schedule; correct top-fraction
        # seating lands outside the published band, so bands_ok must be false.
        assert got["bands_ok"] is False
        for sid in REQUIRED_IDS:
            depth = float(smap[sid]["avg_depth"])
            assert int(smap[sid]["tip_epoch"]) == state["epoch"]
            assert abs(float(smap[sid]["capacity"]) - state["capacity"]) < 1e-12
            assert abs(depth - state["rows"][sid]["avg_depth"]) < 1e-9
            assert abs(depth - base["rows"][sid]["avg_depth"]) > 1e-6
            assert not (lo <= depth <= hi)


def test_m2_andesite():
    """tip_bind.accept matches the registry-resolved durable tip."""
    accept = Path("/app/calib/tip_bind.accept")
    assert accept.is_file()
    vals = {}
    for line in accept.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip().strip('"')
    tip = _resolve_tip(_journal_rows(DATA_ROOT), _retired_tips(DATA_ROOT))
    assert vals.get("tip") == tip["tip"]
    assert int(vals.get("epoch", "-1")) == int(tip["epoch"])
    assert abs(float(vals.get("capacity", "nan")) - float(tip["capacity"])) < 1e-12


def test_n8_basalt():
    """Stale schedule_mirror depth values land outside the published band."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    cap = state["capacity"]
    shallow, deep = _schedule(DATA_ROOT, cap, mirror=True)
    lo, hi = DEPTH_BAND
    for sid, sc in _scenarios(DATA_ROOT).items():
        scores = [float(v) for v in sc["token_scores"]]
        mirrored = _avg_depth(scores, cap, shallow, deep)
        published = float(_scenario_map(report)[sid]["avg_depth"])
        assert not (lo <= mirrored <= hi)
        assert lo <= published <= hi
        assert abs(published - mirrored) > 1e-6
