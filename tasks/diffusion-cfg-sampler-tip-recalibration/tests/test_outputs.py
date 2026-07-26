"""Verifier for diffusion-cfg-sampler-tip-recalibration.

Grades /output/diff-eval.json against published bands, faithful-engine
metrics on frozen fixtures, entrypoint republish, and a novel tip inject.
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

REPORT = Path("/output/diff-eval.json")
ENTRY = "/app/scripts/run_diff_eval.sh"
PIN = Path(__file__).resolve().parent / "data.sha256"
RERUN1 = Path("/logs/verifier/diff-eval-rerun1.json")
RERUN2 = Path("/logs/verifier/diff-eval-rerun2.json")
DATA_ROOT = "/app/data"
DOCS_ROOT = "/app/docs"

IDS = ("cold_a", "resume_a", "cold_b", "resume_b", "mix_c", "mix_d")

CFG_EXPECTED = 7.5
CFG_TOL = 1e-6
SAMPLER_EXPECTED = "dpmpp_2m"
EPOCH_EXPECTED = 6
PARITY_TOL = 1e-4
F_TOL = 1e-6
C_TOL = 1e-3
CFG_BAND = (7.40, 7.60)

# fid = 100 * (1 - recall@10) under the bound durable tip.
EXPECTED = {
    "cold_a": (6.250000, 0.536071),
    "resume_a": (6.250000, 0.536071),
    "cold_b": (6.250000, 0.507047),
    "resume_b": (6.250000, 0.507047),
    "mix_c": (17.187500, 0.525973),
    "mix_d": (17.187500, 0.493897),
}

BANDS = {
    "cold_a": (5.000, 8.000, 0.512, 0.556),
    "resume_a": (5.000, 8.000, 0.512, 0.556),
    "cold_b": (5.000, 8.000, 0.483, 0.528),
    "resume_b": (5.000, 8.000, 0.483, 0.528),
    "mix_c": (15.000, 20.000, 0.501, 0.547),
    "mix_d": (15.000, 20.000, 0.470, 0.514),
}

BAIT = {
    "cold_a": (7.040000, 0.543900),
    "resume_a": (7.040000, 0.543900),
    "cold_b": (7.590000, 0.502800),
    "resume_b": (7.590000, 0.502800),
    "mix_c": (16.710000, 0.526100),
    "mix_d": (15.360000, 0.491700),
}

NOVEL_TIP = {
    "idx": 10,
    "state": "durable",
    "tip": "tip_g10",
    "sheet": "a7",
    "weft_c": [
        "bank_a/seg_01",
        "bank_a/seg_03",
        "bank_b/seg_02",
        "bank_b/seg_04",
    ],
    "weft_d": [
        "bank_a/seg_02",
        "bank_a/seg_04",
        "bank_b/seg_01",
        "bank_b/seg_03",
    ],
    "note": "novel inject",
}
NOVEL_CFG = 7.680000
NOVEL_SAMPLER = "dpmpp_2m"


def _finite(v):
    return float("-inf") < float(v) < float("inf")


def _load_report():
    assert REPORT.is_file(), "missing /output/diff-eval.json"
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _cells(doc):
    scen = doc.get("scenarios")
    assert isinstance(scen, list), "scenarios must be an array"
    got = [c.get("id") for c in scen]
    assert got == list(IDS), f"scenario ids/order mismatch: {got}"
    return {c["id"]: c for c in scen}


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
    """Frozen banks, checkpoints, tip journal, schedules, fixture, and
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
    """Report carries diff-eval-v2, the six scenario ids in order, typed
    metric fields, sampler strings, and integer tip_epoch."""
    doc = _load_report()
    assert doc.get("schema_tag") == "diff-eval-v2"
    assert isinstance(doc.get("bands_ok"), bool)
    cells = _cells(doc)
    for cid in IDS:
        c = cells[cid]
        for key in ("fid", "clip_score", "cfg_scale"):
            v = c.get(key)
            assert isinstance(v, (int, float)) and not isinstance(v, bool), (
                f"{cid}.{key} must be a number"
            )
            assert _finite(v), f"{cid}.{key} must be finite"
        assert isinstance(c.get("sampler"), str) and c["sampler"], (
            f"{cid}.sampler must be a non-empty string"
        )
        e = c.get("tip_epoch")
        assert isinstance(e, int) and not isinstance(e, bool), (
            f"{cid}.tip_epoch must be an integer"
        )


def test_p7_jasper():
    """Resume scenarios reproduce cold twins: fid and clip_score within 1e-4."""
    cells = _cells(_load_report())
    for fam in ("a", "b"):
        cold = cells[f"cold_{fam}"]
        res = cells[f"resume_{fam}"]
        df = abs(float(cold["fid"]) - float(res["fid"]))
        dc = abs(float(cold["clip_score"]) - float(res["clip_score"]))
        assert df <= PARITY_TOL, f"family {fam}: fid parity broken (|d|={df})"
        assert dc <= PARITY_TOL, f"family {fam}: clip parity broken (|d|={dc})"


def test_w1_topaz():
    """cfg_scale and sampler match the durable schedule pair for the bound tip."""
    cells = _cells(_load_report())
    for cid in IDS:
        cfg = float(cells[cid]["cfg_scale"])
        assert CFG_BAND[0] <= cfg <= CFG_BAND[1], (
            f"{cid}.cfg_scale {cfg} outside published CFG band"
        )
        assert abs(cfg - CFG_EXPECTED) <= CFG_TOL, (
            f"{cid}.cfg_scale {cfg} is not the durable schedule CFG"
        )
        assert cells[cid]["sampler"] == SAMPLER_EXPECTED, (
            f"{cid}.sampler {cells[cid]['sampler']!r} is not the durable sampler"
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
        want_f, want_c = EXPECTED[cid]
        got_f = float(cells[cid]["fid"])
        got_c = float(cells[cid]["clip_score"])
        assert abs(got_f - want_f) <= F_TOL, (
            f"{cid}.fid {got_f} != engine value {want_f}"
        )
        assert abs(got_c - want_c) <= C_TOL, (
            f"{cid}.clip_score {got_c} != engine value {want_c}"
        )


def test_r3_garnet():
    """cold_a / cold_b match faithful-engine values under the bound tip."""
    _assert_cells_match(("cold_a", "cold_b"))


def test_t6_beryl():
    """resume_a / resume_b match faithful-engine values; fails when VAE
    block-scale frames unpack into displaced geometry."""
    _assert_cells_match(("resume_a", "resume_b"))


def test_m5_onyx():
    """mix_c / mix_d match faithful-engine values; fails when mixes fold
    segments outside the bound tip roster."""
    _assert_cells_match(("mix_c", "mix_d"))


def test_g6_coral():
    """Every scenario sits inside its published band and bands_ok is true."""
    doc = _load_report()
    cells = _cells(doc)
    for cid in IDS:
        f_lo, f_hi, c_lo, c_hi = BANDS[cid]
        f = float(cells[cid]["fid"])
        c = float(cells[cid]["clip_score"])
        assert f_lo <= f <= f_hi, f"{cid}.fid {f} outside published band"
        assert c_lo <= c <= c_hi, f"{cid}.clip_score {c} outside published band"
    assert doc.get("bands_ok") is True, "bands_ok must be true"


def test_h3_umber():
    """Stale surface-sweep artifact (teacher-forced short sampler) must not
    be the source of the published numbers."""
    cells = _cells(_load_report())
    for cid in IDS:
        bait_f, bait_c = BAIT[cid]
        got = (float(cells[cid]["fid"]), float(cells[cid]["clip_score"]))
        copied = abs(got[0] - bait_f) <= 1e-9 and abs(got[1] - bait_c) <= 1e-9
        assert not copied, f"{cid} copies the stale surface-sweep artifact"
        assert cells[cid]["sampler"] != "euler_short", (
            f"{cid}.sampler copies the surface-sweep short sampler"
        )


def test_d9_quartz():
    """Re-running the entrypoint twice reproduces /output/diff-eval.json."""
    published = REPORT.read_bytes()
    _republish(RERUN1)
    assert RERUN1.read_bytes() == published, (
        "republish through the entrypoint does not reproduce "
        "/output/diff-eval.json"
    )
    _republish(RERUN2)
    assert RERUN2.read_bytes() == published, (
        "two consecutive entrypoint runs are not byte-identical"
    )


def test_n8_zircon():
    """A novel durable tip shifts tip_epoch, cfg_scale, and mix metrics."""
    base = _cells(_load_report())
    base_mix = (
        float(base["mix_c"]["fid"]),
        float(base["mix_d"]["fid"]),
    )
    tmp = Path(tempfile.mkdtemp(prefix="diff-novel-"))
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
            cfg_done = False
            samp_done = False
            for line in text.splitlines(keepends=True):
                stripped = line.strip()
                if stripped == "[cfg]":
                    section = "cfg"
                    rebuilt.append(line)
                    continue
                if stripped == "[sampler]":
                    if section == "cfg" and not cfg_done:
                        rebuilt.append(f'"10" = {NOVEL_CFG:.6f}\n')
                        cfg_done = True
                    section = "sampler"
                    rebuilt.append(line)
                    continue
                rebuilt.append(line)
            if not cfg_done:
                rebuilt.append(f'"10" = {NOVEL_CFG:.6f}\n')
            if not samp_done:
                rebuilt.append(f'"10" = "{NOVEL_SAMPLER}"\n')
                samp_done = True
            table.write_text("".join(rebuilt), encoding="utf-8")
        out = tmp / "novel-eval.json"
        _run_eval_on_root(root, out)
        doc = json.loads(out.read_text(encoding="utf-8"))
        cells = {c["id"]: c for c in doc["scenarios"]}
        for cid in IDS:
            assert cells[cid]["tip_epoch"] == 10, (
                f"{cid}.tip_epoch did not follow novel tip"
            )
            assert abs(float(cells[cid]["cfg_scale"]) - NOVEL_CFG) <= CFG_TOL, (
                f"{cid}.cfg_scale did not follow novel tip"
            )
            assert cells[cid]["sampler"] == NOVEL_SAMPLER, (
                f"{cid}.sampler did not follow novel tip"
            )
        novel_mix = (
            float(cells["mix_c"]["fid"]),
            float(cells["mix_d"]["fid"]),
        )
        assert novel_mix != base_mix, "novel tip must move mix composition"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
