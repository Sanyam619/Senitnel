"""Verifier for cross-encoder-rerank-calibration.

Grades /output/rerank-eval.json against published bands, faithful-engine
metrics on frozen fixtures, entrypoint republish, and a novel tip inject.
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

REPORT = Path("/output/rerank-eval.json")
ENTRY = "/app/scripts/run_rerank_eval.sh"
PIN = Path(__file__).resolve().parent / "data.sha256"
RERUN1 = Path("/logs/verifier/rerank-eval-rerun1.json")
RERUN2 = Path("/logs/verifier/rerank-eval-rerun2.json")
DATA_ROOT = "/app/data"
DOCS_ROOT = "/app/docs"

IDS = ("cold_a", "resume_a", "cold_b", "resume_b", "mix_c", "mix_d")

TEMP_EXPECTED = 0.125
TEMP_TOL = 1e-6
FUSION_EXPECTED = "rrf"
EPOCH_EXPECTED = 6
PARITY_TOL = 1e-4
N_TOL = 1e-6
M_TOL = 1e-3
TEMP_BAND = (0.118, 0.131)

# ndcg_at_10 = recall@10 under the bound durable tip; mrr = seating agreement.
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
        "pool_a/seg_01",
        "pool_a/seg_03",
        "pool_b/seg_02",
        "pool_b/seg_04",
    ],
    "weft_d": [
        "pool_a/seg_02",
        "pool_a/seg_04",
        "pool_b/seg_01",
        "pool_b/seg_03",
    ],
    "note": "novel inject",
}
NOVEL_TEMP = 0.128000
NOVEL_FUSION = "rrf"


def _finite(v):
    return float("-inf") < float(v) < float("inf")


def _load_report():
    assert REPORT.is_file(), "missing /output/rerank-eval.json"
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _cells(doc):
    slices = doc.get("slices")
    assert isinstance(slices, list), "slices must be an array"
    got = [c.get("id") for c in slices]
    assert got == list(IDS), f"slice ids/order mismatch: {got}"
    return {c["id"]: c for c in slices}


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


def test_j2_pyrite():
    """Frozen pools, packs, qrels, tip journal, schedules, fixture, and
    published bands keep their shipped digests."""
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


def test_k4_agate():
    """Report carries rerank-eval-v1, the six slice ids in order, typed
    metric fields, fusion strings, and integer tip_epoch."""
    doc = _load_report()
    assert doc.get("schema_tag") == "rerank-eval-v1"
    assert isinstance(doc.get("eval_ok"), bool)
    cells = _cells(doc)
    for cid in IDS:
        c = cells[cid]
        for key in ("ndcg_at_10", "mrr", "temperature"):
            v = c.get(key)
            assert isinstance(v, (int, float)) and not isinstance(v, bool), (
                f"{cid}.{key} must be a number"
            )
            assert _finite(v), f"{cid}.{key} must be finite"
        assert isinstance(c.get("fusion"), str) and c["fusion"], (
            f"{cid}.fusion must be a non-empty string"
        )
        assert c["fusion"] in ("rrf", "linear", "learned"), (
            f"{cid}.fusion {c['fusion']!r} not in rrf|linear|learned"
        )
        e = c.get("tip_epoch")
        assert isinstance(e, int) and not isinstance(e, bool), (
            f"{cid}.tip_epoch must be an integer"
        )


def test_p7_jasper():
    """Resume slices reproduce cold twins: ndcg_at_10 and mrr within 1e-4."""
    cells = _cells(_load_report())
    for fam in ("a", "b"):
        cold = cells[f"cold_{fam}"]
        res = cells[f"resume_{fam}"]
        dn = abs(float(cold["ndcg_at_10"]) - float(res["ndcg_at_10"]))
        dm = abs(float(cold["mrr"]) - float(res["mrr"]))
        assert dn <= PARITY_TOL, f"family {fam}: ndcg parity broken (|d|={dn})"
        assert dm <= PARITY_TOL, f"family {fam}: mrr parity broken (|d|={dm})"


def test_w1_topaz():
    """temperature and fusion match the durable schedule pair for the tip."""
    cells = _cells(_load_report())
    for cid in IDS:
        temp = float(cells[cid]["temperature"])
        assert TEMP_BAND[0] <= temp <= TEMP_BAND[1], (
            f"{cid}.temperature {temp} outside published temperature band"
        )
        assert abs(temp - TEMP_EXPECTED) <= TEMP_TOL, (
            f"{cid}.temperature {temp} is not the durable schedule temperature"
        )
        assert cells[cid]["fusion"] == FUSION_EXPECTED, (
            f"{cid}.fusion {cells[cid]['fusion']!r} is not the durable fusion"
        )


def test_v8_lazuli():
    """tip_epoch equals the bound durable tip generation."""
    cells = _cells(_load_report())
    for cid in IDS:
        e = cells[cid]["tip_epoch"]
        assert e == EPOCH_EXPECTED, (
            f"{cid}.tip_epoch {e} is not the bound durable generation"
        )


def test_q1_flint():
    """Retired newest-durable and live sweep tips must not be the bound tip."""
    cells = _cells(_load_report())
    for cid in IDS:
        e = cells[cid]["tip_epoch"]
        assert e != 8, f"{cid}.tip_epoch binds retired tip_g9"
        assert e != 9, f"{cid}.tip_epoch binds live tip"


def _assert_cells_match(cids):
    cells = _cells(_load_report())
    for cid in cids:
        want_n, want_m = EXPECTED[cid]
        got_n = float(cells[cid]["ndcg_at_10"])
        got_m = float(cells[cid]["mrr"])
        assert abs(got_n - want_n) <= N_TOL, (
            f"{cid}.ndcg_at_10 {got_n} != engine value {want_n}"
        )
        assert abs(got_m - want_m) <= M_TOL, (
            f"{cid}.mrr {got_m} != engine value {want_m}"
        )


def test_r3_garnet():
    """cold_a / cold_b match faithful-engine values under the bound tip."""
    _assert_cells_match(("cold_a", "cold_b"))


def test_t6_beryl():
    """resume_a / resume_b match faithful-engine values; fails when packed
    score frames unpack into displaced geometry."""
    _assert_cells_match(("resume_a", "resume_b"))


def test_m5_onyx():
    """mix_c / mix_d match faithful-engine values; fails when mixes fold
    segments outside the bound tip roster."""
    _assert_cells_match(("mix_c", "mix_d"))


def test_g6_coral():
    """Every slice sits inside its published band and eval_ok is true."""
    doc = _load_report()
    cells = _cells(doc)
    for cid in IDS:
        n_lo, n_hi, m_lo, m_hi = BANDS[cid]
        n = float(cells[cid]["ndcg_at_10"])
        m = float(cells[cid]["mrr"])
        assert n_lo <= n <= n_hi, f"{cid}.ndcg_at_10 {n} outside published band"
        assert m_lo <= m <= m_hi, f"{cid}.mrr {m} outside published band"
    assert doc.get("eval_ok") is True, "eval_ok must be true"


def test_h3_umber():
    """Stale surface-sweep artifact (linear fusion bait) must not be the
    source of the published numbers; first-stage probe is not authority."""
    cells = _cells(_load_report())
    for cid in IDS:
        bait_n, bait_m = BAIT[cid]
        got = (float(cells[cid]["ndcg_at_10"]), float(cells[cid]["mrr"]))
        copied = abs(got[0] - bait_n) <= 1e-9 and abs(got[1] - bait_m) <= 1e-9
        assert not copied, f"{cid} copies the stale surface-sweep artifact"
        assert cells[cid]["fusion"] != "linear", (
            f"{cid}.fusion copies the surface-sweep linear fusion"
        )
    proc = subprocess.run(
        ["/app/tools/rerankprobe"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "first-stage: pass" in proc.stdout


def test_d9_quartz():
    """Re-running the entrypoint twice reproduces /output/rerank-eval.json."""
    published = REPORT.read_bytes()
    _republish(RERUN1)
    assert RERUN1.read_bytes() == published, (
        "republish through the entrypoint does not reproduce "
        "/output/rerank-eval.json"
    )
    _republish(RERUN2)
    assert RERUN2.read_bytes() == published, (
        "two consecutive entrypoint runs are not byte-identical"
    )


def test_n8_zircon():
    """A novel durable tip shifts tip_epoch, temperature, fusion, and mix."""
    base = _cells(_load_report())
    base_mix = (
        float(base["mix_c"]["ndcg_at_10"]),
        float(base["mix_d"]["ndcg_at_10"]),
    )
    tmp = Path(tempfile.mkdtemp(prefix="rerank-novel-"))
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
            rebuilt = []
            section = ""
            temp_done = False
            fus_done = False
            for line in text.splitlines(keepends=True):
                stripped = line.strip()
                if stripped == "[temperature]":
                    section = "temperature"
                    rebuilt.append(line)
                    continue
                if stripped == "[fusion]":
                    if section == "temperature" and not temp_done:
                        rebuilt.append(f'"10" = {NOVEL_TEMP:.6f}\n')
                        temp_done = True
                    section = "fusion"
                    rebuilt.append(line)
                    continue
                rebuilt.append(line)
            if not temp_done:
                rebuilt.append(f'"10" = {NOVEL_TEMP:.6f}\n')
            if not fus_done:
                rebuilt.append(f'"10" = "{NOVEL_FUSION}"\n')
                fus_done = True
            table.write_text("".join(rebuilt), encoding="utf-8")
        out = tmp / "novel-eval.json"
        _run_eval_on_root(root, out)
        doc = json.loads(out.read_text(encoding="utf-8"))
        cells = {c["id"]: c for c in doc["slices"]}
        for cid in IDS:
            assert cells[cid]["tip_epoch"] == 10, (
                f"{cid}.tip_epoch did not follow novel tip"
            )
            assert abs(float(cells[cid]["temperature"]) - NOVEL_TEMP) <= TEMP_TOL, (
                f"{cid}.temperature did not follow novel tip"
            )
            assert cells[cid]["fusion"] == NOVEL_FUSION, (
                f"{cid}.fusion did not follow novel tip"
            )
        novel_mix = (
            float(cells["mix_c"]["ndcg_at_10"]),
            float(cells["mix_d"]["ndcg_at_10"]),
        )
        assert novel_mix != base_mix, "novel tip must move mix composition"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
