"""Verifier tests for the speech diarization DER calibration report."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

REPORT_PATH = "/output/diar-eval.json"
BINARY_PATH = "/app/eng/target/release/diar-eval"
DATA_ROOT = Path("/app/data")
CRATE_ROOT = Path("/app/eng")
SCHEMA_TAG = "diar-eval-v1"
SLICE_ORDER = ("s_meet_a", "s_meet_b", "s_call_c", "s_call_d", "s_far_e")
DER_BANDS = {
    "s_meet_a": (0.092, 0.104),
    "s_meet_b": (0.106, 0.118),
    "s_call_c": (0.081, 0.093),
    "s_call_d": (0.119, 0.131),
    "s_far_e": (0.135, 0.147),
}
JER_BANDS = {
    "s_meet_a": (0.126, 0.138),
    "s_meet_b": (0.142, 0.154),
    "s_call_c": (0.115, 0.127),
    "s_call_d": (0.155, 0.167),
    "s_far_e": (0.172, 0.184),
}
DURABLE_METHODS = ("ahc", "spectral", "nme")
NOVEL_JOURNAL_ROW = {
    "tip": "tip_n5",
    "epoch": 10,
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


def _journal_rows(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _retired_tips(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    out = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.add(json.loads(line)["tip"])
    return out


def _resolve_embed(root: Path) -> dict:
    rows = _journal_rows(root / "embed_registry" / "tip_journal.jsonl")
    retired = _retired_tips(root / "embed_registry" / "retired_tips.jsonl")
    best = None
    for row in rows:
        if not row.get("sealed"):
            continue
        if row.get("tip") in retired:
            continue
        if best is None or int(row["epoch"]) >= int(best["epoch"]):
            best = row
    assert best is not None, "embed journal has no selectable sealed tip"
    return best


def _resolve_cluster(root: Path) -> dict:
    rows = _journal_rows(root / "cluster_registry" / "tip_journal.jsonl")
    retired = _retired_tips(root / "cluster_registry" / "retired_tips.jsonl")
    best = None
    for row in rows:
        if not row.get("sealed"):
            continue
        if row.get("tip") in retired:
            continue
        if best is None or int(row["epoch"]) >= int(best["epoch"]):
            best = row
    assert best is not None, "cluster journal has no selectable sealed tip"
    return best


def _slice_fixtures(root: Path) -> list[dict]:
    rows = []
    for path in sorted((root / "audio").glob("*.json")):
        rows.append(_read_json(path))
    rows.sort(key=lambda r: int(r["seq"]))
    return rows


def _column_key(method: str, epoch: int) -> str:
    return f"{method}_e{epoch}"


def _metrics(fx: dict, method: str, epoch: int) -> tuple[float, float]:
    key = _column_key(method, epoch)
    return float(fx[f"der_{key}"]), float(fx[f"jer_{key}"])


def _expected_state(root: Path) -> dict:
    tip = _resolve_embed(root)
    cluster = _resolve_cluster(root)
    method = cluster["clustering"]
    epoch = int(tip["epoch"])
    fixtures = _slice_fixtures(root)
    slices = []
    for fx in fixtures:
        der, jer = _metrics(fx, method, epoch)
        slices.append(
            {
                "id": fx["id"],
                "der": der,
                "jer": jer,
                "clustering": method,
                "tip_epoch": epoch,
            }
        )
    return {
        "tip": tip,
        "cluster": cluster,
        "method": method,
        "slices": slices,
        "fixtures": fixtures,
    }


def _load_report() -> dict:
    _assert_fixtures_intact()
    assert Path(REPORT_PATH).is_file(), "missing /output/diar-eval.json"
    return _read_json(REPORT_PATH)


def _assert_bands(report: dict) -> None:
    by_id = {row["id"]: row for row in report["slices"]}
    for sid, (lo, hi) in DER_BANDS.items():
        der = float(by_id[sid]["der"])
        assert lo <= der <= hi, f"{sid} der {der} outside [{lo}, {hi}]"
    for sid, (lo, hi) in JER_BANDS.items():
        jer = float(by_id[sid]["jer"])
        assert lo <= jer <= hi, f"{sid} jer {jer} outside [{lo}, {hi}]"
    assert report["eval_ok"] is True


def test_a3_garnet():
    """Frozen audio, RTTM, and tip registries match fixtures.sha256."""
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
        assert set(row) >= {"id", "der", "jer", "clustering", "tip_epoch"}
        assert isinstance(row["id"], str)
        assert float("-inf") < float(row["der"]) < float("inf")
        assert float("-inf") < float(row["jer"]) < float("inf")
        assert not isinstance(row["tip_epoch"], (str, bool))
        assert float(row["tip_epoch"]) == int(row["tip_epoch"])
        assert isinstance(row["clustering"], str)


def test_c1_biotite():
    """tip_epoch on every slice carries the sealed, non-retired embed tip epoch."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    for row in report["slices"]:
        assert int(row["tip_epoch"]) == int(state["tip"]["epoch"])


def test_d9_epidote():
    """Published tip is neither the retired sealed-max nor the live observational epoch."""
    report = _load_report()
    rows = _journal_rows(DATA_ROOT / "embed_registry" / "tip_journal.jsonl")
    retired = _retired_tips(DATA_ROOT / "embed_registry" / "retired_tips.jsonl")
    sealed_max = max(
        (row for row in rows if row.get("sealed")),
        key=lambda r: int(r["epoch"]),
    )
    assert sealed_max["tip"] in retired, "fixture must bait sealed-max with a retired tip"
    live_epochs = {int(row["epoch"]) for row in rows if row["tip"] == "tip_live"}
    state = _expected_state(DATA_ROOT)
    assert int(state["tip"]["epoch"]) != int(sealed_max["epoch"])
    assert int(state["tip"]["epoch"]) not in live_epochs
    published = {int(row["tip_epoch"]) for row in report["slices"]}
    assert published == {int(state["tip"]["epoch"])}
    assert int(sealed_max["epoch"]) not in published
    assert not (published & live_epochs)


def test_e2_scoria():
    """clustering on every slice is the durable method tip, not the live decoy."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    want = state["method"]
    assert want in DURABLE_METHODS
    live_rows = [
        row
        for row in _journal_rows(DATA_ROOT / "cluster_registry" / "tip_journal.jsonl")
        if row["tip"] == "tip_live"
    ]
    assert live_rows, "fixture must include a live clustering decoy"
    live_method = live_rows[0]["clustering"]
    assert want != live_method
    for row in report["slices"]:
        assert row["clustering"] == want
        assert row["clustering"] != live_method


def test_f5_dolomite():
    """Per-slice der and jer match the durable method×epoch scored columns."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    by_id = {row["id"]: row for row in report["slices"]}
    for want in state["slices"]:
        got = by_id[want["id"]]
        assert abs(float(got["der"]) - want["der"]) <= 1e-6
        assert abs(float(got["jer"]) - want["jer"]) <= 1e-6


def test_g8_feldspar():
    """Every slice lands inside its published band and eval_ok is true."""
    _assert_bands(_load_report())


def test_i6_marl():
    """Oracle-count DER path misses at least one published DER band."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    fixtures_by_id = {fx["id"]: fx for fx in state["fixtures"]}
    first_id = SLICE_ORDER[0]
    by_id = {row["id"]: row for row in report["slices"]}
    got = float(by_id[first_id]["der"])
    lo, hi = DER_BANDS[first_id]
    assert lo <= got <= hi
    oracle_der = float(fixtures_by_id[first_id]["der_oracle"])
    assert not (lo <= oracle_der <= hi), "fixture must make the oracle-count path miss der band"
    assert abs(got - oracle_der) > 1e-6


def test_n8_basalt():
    """The stale ledger method mirror is not the scored-column authority."""
    report = _load_report()
    state = _expected_state(DATA_ROOT)
    mirror = _read_json(DATA_ROOT / "ledger" / "method_mirror.json")
    mapping = {row["name"]: row["column_prefix"] for row in mirror["methods"]}
    stale_prefix = mapping[state["method"]]
    assert stale_prefix != state["method"], "fixture must keep a divergent mirror mapping"
    fixtures_by_id = {fx["id"]: fx for fx in state["fixtures"]}
    by_id = {row["id"]: row for row in report["slices"]}
    epoch = int(state["tip"]["epoch"])
    for sid in SLICE_ORDER:
        stale_der, stale_jer = _metrics(fixtures_by_id[sid], stale_prefix, epoch)
        dlo, dhi = DER_BANDS[sid]
        jlo, jhi = JER_BANDS[sid]
        assert not (dlo <= stale_der <= dhi and jlo <= stale_jer <= jhi)
        assert abs(float(by_id[sid]["der"]) - stale_der) > 1e-6
        assert abs(float(by_id[sid]["jer"]) - stale_jer) > 1e-6


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
    """A novel sealed embed tip moves tip_epoch and the scored method×epoch columns."""
    _assert_fixtures_intact()
    tmp_root = Path(tempfile.mkdtemp(prefix="diar-novel-"))
    try:
        shutil.copytree(DATA_ROOT / "audio", tmp_root / "audio")
        shutil.copytree(DATA_ROOT / "embed_registry", tmp_root / "embed_registry")
        shutil.copytree(DATA_ROOT / "cluster_registry", tmp_root / "cluster_registry")
        shutil.copytree(DATA_ROOT / "ledger", tmp_root / "ledger")
        journal = tmp_root / "embed_registry" / "tip_journal.jsonl"
        with open(journal, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(NOVEL_JOURNAL_ROW) + "\n")

        base_state = _expected_state(DATA_ROOT)
        state = _expected_state(tmp_root)
        assert int(state["tip"]["epoch"]) == int(NOVEL_JOURNAL_ROW["epoch"])
        assert int(state["tip"]["epoch"]) != int(base_state["tip"]["epoch"])
        assert state["method"] == base_state["method"]

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
                assert int(got["tip_epoch"]) == int(state["tip"]["epoch"])
                assert got["clustering"] == state["method"]
                assert abs(float(got["der"]) - want["der"]) <= 1e-6
                assert abs(float(got["jer"]) - want["jer"]) <= 1e-6
                base_row = base_by_id[want["id"]]
                assert abs(float(got["der"]) - base_row["der"]) > 1e-6
                assert abs(float(got["jer"]) - base_row["jer"]) > 1e-6
        finally:
            os.unlink(out)
    finally:
        shutil.rmtree(tmp_root)


def test_m2_andesite():
    """Durable tip bind receipt must name the registry-resolved tips and clustering."""
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
    assert pairs.get("clustering") == state["method"]
    assert pairs.get("method") == state["cluster"]["tip"]
    for row in report["slices"]:
        assert row["clustering"] == pairs["clustering"]
        assert int(row["tip_epoch"]) == int(pairs["epoch"])
