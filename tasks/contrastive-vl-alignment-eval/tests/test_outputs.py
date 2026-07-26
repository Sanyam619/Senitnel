"""Verifier for contrastive-vl-alignment-eval.

Grades /output/vl-eval.json against published bands, faithful-engine
metrics on frozen fixtures, entrypoint republish, and a novel tip inject.
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

REPORT = Path("/output/vl-eval.json")
ENTRY = "/app/scripts/run_vl_eval.sh"
PIN = Path(__file__).resolve().parent / "data.sha256"
RERUN1 = Path("/tmp/vl-eval-rerun1.json")
RERUN2 = Path("/tmp/vl-eval-rerun2.json")
DATA_ROOT = "/app/data"
DOCS_ROOT = "/app/docs"

IDS = ("cold_a", "resume_a", "cold_b", "resume_b", "mix_c", "mix_d")

TEMP_EXPECTED = 0.125
TEMP_TOL = 1e-6
POOL_EXPECTED = "hardmine"
EPOCH_EXPECTED = 6
PARITY_TOL = 1e-4
R_TOL = 1e-6
TEMP_BAND = (0.118, 0.131)

EXPECTED = {
    "cold_a": (0.937500, 0.937500),
    "resume_a": (0.937500, 0.937500),
    "cold_b": (0.937500, 0.937500),
    "resume_b": (0.937500, 0.937500),
    "mix_c": (0.812500, 0.828125),
    "mix_d": (0.812500, 0.828125),
}

BANDS = {
    "cold_a": (0.900, 0.970, 0.910, 0.970),
    "resume_a": (0.900, 0.970, 0.910, 0.970),
    "cold_b": (0.900, 0.970, 0.910, 0.970),
    "resume_b": (0.900, 0.970, 0.910, 0.970),
    "mix_c": (0.760, 0.860, 0.800, 0.870),
    "mix_d": (0.760, 0.860, 0.800, 0.870),
}

BAIT = {
    "cold_a": (0.718750, 0.929600),
    "resume_a": (0.718750, 0.929600),
    "cold_b": (0.703125, 0.924100),
    "resume_b": (0.703125, 0.924100),
    "mix_c": (0.640625, 0.832900),
    "mix_d": (0.656250, 0.846400),
}

NOVEL_TEMP = 0.128000
NOVEL_POOL = "hardmine"


def _novel_tip():
    """Build a novel durable tip whose mix wefts reuse an existing sealed
    tip roster (read from the frozen journal, not hardcoded in the suite)."""
    journal = Path(DATA_ROOT) / "feature_registry" / "tip_journal.jsonl"
    base = None
    for line in journal.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("tip") == "tip_g3":
            base = row
            break
    assert base is not None, "missing tip_g3 roster for novel inject"
    return {
        "idx": 10,
        "state": "durable",
        "tip": "tip_g10",
        "sheet": "a7",
        "weft_c": list(base["weft_c"]),
        "weft_d": list(base["weft_d"]),
        "note": "novel inject",
    }


def _finite(v):
    return float("-inf") < float(v) < float("inf")


def _load_report():
    assert REPORT.is_file(), "missing /output/vl-eval.json"
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
    env["PRISM_ROOT"] = str(root)
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
    """Frozen image banks, caption frames, tip journal, schedules, fixture,
    and published bands keep their shipped digests."""
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
    """Report carries vl-eval-v1, the six slice ids in order, typed metric
    fields, pool strings, and integer tip_epoch."""
    doc = _load_report()
    assert doc.get("schema_tag") == "vl-eval-v1"
    assert isinstance(doc.get("eval_ok"), bool)
    cells = _cells(doc)
    for cid in IDS:
        c = cells[cid]
        for key in ("recall_at_5", "recall_at_10", "temperature"):
            v = c.get(key)
            assert isinstance(v, (int, float)) and not isinstance(v, bool), (
                f"{cid}.{key} must be a number"
            )
            assert _finite(v), f"{cid}.{key} must be finite"
        assert isinstance(c.get("pool"), str) and c["pool"], (
            f"{cid}.pool must be a non-empty string"
        )
        assert c["pool"] in ("inbatch", "hardmine"), (
            f"{cid}.pool {c['pool']!r} not in inbatch|hardmine"
        )
        e = c.get("tip_epoch")
        assert isinstance(e, int) and not isinstance(e, bool), (
            f"{cid}.tip_epoch must be an integer"
        )


def test_p7_jasper():
    """Resume slices reproduce cold twins: recall_at_5 and recall_at_10
    within 1e-4."""
    cells = _cells(_load_report())
    for fam in ("a", "b"):
        cold = cells[f"cold_{fam}"]
        res = cells[f"resume_{fam}"]
        d5 = abs(float(cold["recall_at_5"]) - float(res["recall_at_5"]))
        d10 = abs(float(cold["recall_at_10"]) - float(res["recall_at_10"]))
        assert d5 <= PARITY_TOL, f"family {fam}: recall@5 parity broken (|d|={d5})"
        assert d10 <= PARITY_TOL, (
            f"family {fam}: recall@10 parity broken (|d|={d10})"
        )


def test_w1_topaz():
    """temperature and pool match the durable schedule pair for the tip."""
    cells = _cells(_load_report())
    for cid in IDS:
        temp = float(cells[cid]["temperature"])
        assert TEMP_BAND[0] <= temp <= TEMP_BAND[1], (
            f"{cid}.temperature {temp} outside published temperature band"
        )
        assert abs(temp - TEMP_EXPECTED) <= TEMP_TOL, (
            f"{cid}.temperature {temp} is not the durable logit-scale tip"
        )
        assert cells[cid]["pool"] == POOL_EXPECTED, (
            f"{cid}.pool {cells[cid]['pool']!r} is not the durable negative pool"
        )


def test_v8_lazuli():
    """tip_epoch equals the sealed durable bank tip generation."""
    cells = _cells(_load_report())
    for cid in IDS:
        e = cells[cid]["tip_epoch"]
        assert e == EPOCH_EXPECTED, (
            f"{cid}.tip_epoch {e} is not the bound durable generation"
        )


def test_q1_flint():
    """Retired newest-durable and live shadow-bank tips must not be bound."""
    cells = _cells(_load_report())
    for cid in IDS:
        e = cells[cid]["tip_epoch"]
        assert e != 8, f"{cid}.tip_epoch binds retired tip_g9"
        assert e != 9, f"{cid}.tip_epoch binds live shadow tip"


def _assert_cells_match(cids):
    cells = _cells(_load_report())
    for cid in cids:
        want_5, want_10 = EXPECTED[cid]
        got_5 = float(cells[cid]["recall_at_5"])
        got_10 = float(cells[cid]["recall_at_10"])
        assert abs(got_5 - want_5) <= R_TOL, (
            f"{cid}.recall_at_5 {got_5} != engine value {want_5}"
        )
        assert abs(got_10 - want_10) <= R_TOL, (
            f"{cid}.recall_at_10 {got_10} != engine value {want_10}"
        )


def test_r3_garnet():
    """cold_a / cold_b match faithful-engine values under the bound tip."""
    _assert_cells_match(("cold_a", "cold_b"))


def test_t6_beryl():
    """resume_a / resume_b match faithful-engine values; fails when packed
    caption frames unpack into displaced geometry."""
    _assert_cells_match(("resume_a", "resume_b"))


def test_m5_onyx():
    """mix_c / mix_d match faithful-engine values; fails when mixes fold
    image segments outside the bound tip roster or use inbatch scoring."""
    _assert_cells_match(("mix_c", "mix_d"))


def test_g6_coral():
    """Every slice sits inside its published band and eval_ok is true."""
    doc = _load_report()
    cells = _cells(doc)
    for cid in IDS:
        r5_lo, r5_hi, r10_lo, r10_hi = BANDS[cid]
        r5 = float(cells[cid]["recall_at_5"])
        r10 = float(cells[cid]["recall_at_10"])
        assert r5_lo <= r5 <= r5_hi, f"{cid}.recall_at_5 {r5} outside published band"
        assert r10_lo <= r10 <= r10_hi, (
            f"{cid}.recall_at_10 {r10} outside published band"
        )
    assert doc.get("eval_ok") is True, "eval_ok must be true"


def test_h3_umber():
    """Stale surface-sweep artifact (inbatch pool bait) must not be the
    source of the published numbers; train-overlap probe is not authority."""
    cells = _cells(_load_report())
    for cid in IDS:
        bait_5, bait_10 = BAIT[cid]
        got = (float(cells[cid]["recall_at_5"]), float(cells[cid]["recall_at_10"]))
        copied = abs(got[0] - bait_5) <= 1e-9 and abs(got[1] - bait_10) <= 1e-9
        assert not copied, f"{cid} copies the stale surface-sweep artifact"
        assert cells[cid]["pool"] != "inbatch", (
            f"{cid}.pool copies the surface-sweep inbatch seating"
        )
    proc = subprocess.run(
        ["/app/tools/vlprobe"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "overlap: aligned" in proc.stdout


def test_d9_quartz():
    """Re-running the entrypoint twice reproduces /output/vl-eval.json."""
    published = REPORT.read_bytes()
    _republish(RERUN1)
    assert RERUN1.read_bytes() == published, (
        "republish through the entrypoint does not reproduce /output/vl-eval.json"
    )
    _republish(RERUN2)
    assert RERUN2.read_bytes() == published, (
        "two consecutive entrypoint runs are not byte-identical"
    )


def test_n8_zircon():
    """A novel durable tip shifts tip_epoch, temperature, pool, and mix."""
    base = _cells(_load_report())
    base_mix = (
        float(base["mix_c"]["recall_at_10"]),
        float(base["mix_d"]["recall_at_10"]),
    )
    tmp = Path(tempfile.mkdtemp(prefix="vl-novel-"))
    try:
        root = tmp / "app"
        root.mkdir()
        shutil.copytree(DATA_ROOT, root / "data")
        shutil.copytree(DOCS_ROOT, root / "docs")
        journal = root / "data" / "feature_registry" / "tip_journal.jsonl"
        with journal.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(_novel_tip()) + "\n")
        table = root / "data" / "sched" / "table_a7.toml"
        text = table.read_text(encoding="utf-8")
        if '"10"' not in text:
            rebuilt = []
            section = ""
            temp_done = False
            pool_done = False
            for line in text.splitlines(keepends=True):
                stripped = line.strip()
                if stripped == "[temperature]":
                    section = "temperature"
                    rebuilt.append(line)
                    continue
                if stripped == "[pool]":
                    if section == "temperature" and not temp_done:
                        rebuilt.append(f'"10" = {NOVEL_TEMP:.6f}\n')
                        temp_done = True
                    section = "pool"
                    rebuilt.append(line)
                    continue
                rebuilt.append(line)
            if not temp_done:
                rebuilt.append(f'"10" = {NOVEL_TEMP:.6f}\n')
            if not pool_done:
                rebuilt.append(f'"10" = "{NOVEL_POOL}"\n')
                pool_done = True
            table.write_text("".join(rebuilt), encoding="utf-8")
        out = tmp / "out-eval.json"
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
            assert cells[cid]["pool"] == NOVEL_POOL, (
                f"{cid}.pool did not follow novel tip"
            )
        novel_mix = (
            float(cells["mix_c"]["recall_at_10"]),
            float(cells["mix_d"]["recall_at_10"]),
        )
        assert novel_mix != base_mix, "novel tip must move mix composition"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
