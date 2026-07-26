"""Verifier for offline-online-feature-skew-calibration.

Grades /output/feature-eval.json against published skew/slice bands, durable
tip binding, difference-form skew, and entrypoint republish byte-identity.
"""

import json
import subprocess
from pathlib import Path

REPORT = Path("/output/feature-eval.json")
ENTRY = "/app/scripts/run_feature_eval.sh"
PIN = Path(__file__).resolve().parent / "data.sha256"
RERUN1 = Path("/logs/verifier/feature-eval-rerun1.json")
RERUN2 = Path("/logs/verifier/feature-eval-rerun2.json")
SURFACE = Path("/app/data/fixtures/surface_ok.json")

FEAT_IDS = ("f_amt", "f_age", "f_zip", "f_chn", "f_risk")
SLICE_IDS = ("retail", "corporate", "mobile", "holdout")
DURABLE = "tip_g7"

SKEW_CAPS = {
    "f_amt": 0.020,
    "f_age": 0.020,
    "f_zip": 0.015,
    "f_chn": 0.020,
    "f_risk": 0.020,
}

SLICE_BANDS = {
    "retail": (0.66, 0.86, 0.18, 0.28),
    "corporate": (0.66, 0.86, 0.18, 0.28),
    "mobile": (0.66, 0.86, 0.18, 0.28),
    "holdout": (0.66, 0.86, 0.18, 0.24),
}

# Faithful engine values on frozen fixtures with durable binding.
EXPECTED_MEANS = {
    "f_amt": (0.420000, 0.418500),
    "f_age": (0.310000, 0.308000),
    "f_zip": (0.550000, 0.549900),
    "f_chn": (0.180000, 0.179000),
    "f_risk": (0.670000, 0.668000),
}

EXPECTED_SLICES = {
    "retail": (0.708020, 0.228370),
    "corporate": (0.738627, 0.224482),
    "mobile": (0.772571, 0.217978),
    "holdout": (0.714498, 0.228133),
}

MEAN_TOL = 1e-6
METRIC_TOL = 1e-5
SKEW_TOL = 1e-6


def _finite(v):
    return float("-inf") < float(v) < float("inf")


def _sha256(path: Path) -> str:
    proc = subprocess.run(
        ["sha256sum", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.split()[0]


def _load_report():
    assert REPORT.is_file(), "missing /output/feature-eval.json"
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _features(doc):
    feats = doc.get("features")
    assert isinstance(feats, list), "features must be an array"
    got = [c.get("name") for c in feats]
    assert got == list(FEAT_IDS), f"feature names/order mismatch: {got}"
    return {c["name"]: c for c in feats}


def _slices(doc):
    cells = doc.get("slices")
    assert isinstance(cells, list), "slices must be an array"
    got = [c.get("id") for c in cells]
    assert got == list(SLICE_IDS), f"slice ids/order mismatch: {got}"
    return {c["id"]: c for c in cells}


def _republish(dest: Path):
    proc = subprocess.run(
        ["/bin/bash", ENTRY, str(dest)],
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    assert proc.returncode == 0, (
        f"entrypoint republish failed rc={proc.returncode}\n"
        f"stdout:\n{proc.stdout[-2000:]}\nstderr:\n{proc.stderr[-2000:]}"
    )
    assert dest.is_file(), f"republish did not write {dest}"


def test_frozen_inputs_integrity():
    """Verify every frozen input still matches its pinned digest."""
    bad = []
    for line in PIN.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        want, path = line.split(maxsplit=1)
        p = Path(path)
        if not p.is_file():
            bad.append(f"missing {path}")
            continue
        have = _sha256(p)
        if have != want:
            bad.append(f"rewritten {path}")
    assert not bad, "frozen inputs were modified: " + "; ".join(bad)


def test_report_schema_and_order():
    """Require the documented report fields, types, and ordering."""
    doc = _load_report()
    assert doc.get("schema_tag") == "feature-eval/v1"
    assert isinstance(doc.get("calibration_ok"), bool)
    feats = _features(doc)
    for name in FEAT_IDS:
        c = feats[name]
        for key in ("offline_mean", "online_mean", "skew"):
            v = c.get(key)
            assert isinstance(v, (int, float)) and not isinstance(v, bool), (
                f"{name}.{key} must be a number"
            )
            assert _finite(v), f"{name}.{key} must be finite"
        assert isinstance(c.get("source"), str) and c["source"], (
            f"{name}.source must be a non-empty string"
        )
    cells = _slices(doc)
    for sid in SLICE_IDS:
        c = cells[sid]
        for key in ("auc", "brier"):
            v = c.get(key)
            assert isinstance(v, (int, float)) and not isinstance(v, bool), (
                f"{sid}.{key} must be a number"
            )
            assert _finite(v), f"{sid}.{key} must be finite"
            assert 0.0 <= float(v) <= 1.0, f"{sid}.{key} out of range"


def test_feature_skew_inside_published_bands():
    """Check engine means and each published feature-skew cap."""
    doc = _load_report()
    feats = _features(doc)
    for name in FEAT_IDS:
        c = feats[name]
        off_e, on_e = EXPECTED_MEANS[name]
        assert abs(float(c["offline_mean"]) - off_e) <= MEAN_TOL, (
            f"{name}.offline_mean {c['offline_mean']} != engine {off_e}"
        )
        assert abs(float(c["online_mean"]) - on_e) <= MEAN_TOL, (
            f"{name}.online_mean {c['online_mean']} != engine {on_e}"
        )
        skew = float(c["skew"])
        assert abs(skew) <= SKEW_CAPS[name] + 1e-12, (
            f"{name} abs(skew)={abs(skew)} exceeds bound {SKEW_CAPS[name]}"
        )


def test_skew_is_online_minus_offline():
    """Require difference-form skew for every graded feature."""
    feats = _features(_load_report())
    for name in FEAT_IDS:
        c = feats[name]
        want = float(c["online_mean"]) - float(c["offline_mean"])
        assert abs(float(c["skew"]) - want) <= SKEW_TOL, (
            f"{name}.skew {c['skew']} is not online_mean - offline_mean ({want})"
        )


def test_source_is_durable_tip():
    """Require every feature to name the durable online tip."""
    feats = _features(_load_report())
    for name in FEAT_IDS:
        assert feats[name]["source"] == DURABLE, (
            f"{name}.source {feats[name]['source']!r} is not durable tip "
            f"{DURABLE} (registry-resolved serving snapshot)"
        )


def test_source_not_retired_or_live_tip():
    """Reject sources that name a retired snapshot or the live trial line."""
    retired = set()
    rpath = Path("/app/data/feature_registry/retired_tips.jsonl")
    assert rpath.is_file(), "missing retired-tips registry record"
    for line in rpath.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        tip = row.get("tip")
        assert isinstance(tip, str) and tip, f"bad retired-tip row: {line}"
        retired.add(tip)
    feats = _features(_load_report())
    for name in FEAT_IDS:
        src = feats[name]["source"]
        assert src not in retired, (
            f"{name}.source {src!r} names a retired snapshot"
        )
        assert src != "tip_live", (
            f"{name}.source {src!r} names the live trial line"
        )


def test_slice_metrics_inside_published_bands():
    """Check calibration status and all published slice bands."""
    doc = _load_report()
    assert doc.get("calibration_ok") is True
    cells = _slices(doc)
    for sid in SLICE_IDS:
        a_lo, a_hi, b_lo, b_hi = SLICE_BANDS[sid]
        a = float(cells[sid]["auc"])
        b = float(cells[sid]["brier"])
        assert a_lo <= a <= a_hi, f"{sid}.auc {a} outside [{a_lo},{a_hi}]"
        assert b_lo <= b <= b_hi, f"{sid}.brier {b} outside [{b_lo},{b_hi}]"
        ea, eb = EXPECTED_SLICES[sid]
        assert abs(a - ea) <= METRIC_TOL, f"{sid}.auc {a} != engine {ea}"
        assert abs(b - eb) <= METRIC_TOL, f"{sid}.brier {b} != engine {eb}"


def test_holdout_brier_rejects_shadow_high_card():
    """Reject holdout metrics produced by a shadow high-card overlay."""
    cells = _slices(_load_report())
    b = float(cells["holdout"]["brier"])
    # Shadow overlay / live tip binding lands near 0.259; stay on durable.
    assert b <= 0.24 + 1e-12, f"holdout.brier {b} looks like a shadow high-card overlay"
    ea, eb = EXPECTED_SLICES["holdout"]
    assert abs(b - eb) <= METRIC_TOL, f"holdout.brier {b} != durable engine {eb}"
    assert abs(float(cells["holdout"]["auc"]) - ea) <= METRIC_TOL


def test_report_disagrees_with_surface_fixture():
    """Ensure the report was not copied from the stale surface fixture."""
    doc = _load_report()
    bait = json.loads(SURFACE.read_text(encoding="utf-8"))
    disagreed = False
    for a, b in zip(doc["features"], bait["features"], strict=True):
        if abs(float(a["online_mean"]) - float(b["online_mean"])) > 1e-6:
            disagreed = True
        if a.get("source") != b.get("source"):
            disagreed = True
    for a, b in zip(doc["slices"], bait["slices"], strict=True):
        if abs(float(a["auc"]) - float(b["auc"])) > 1e-6:
            disagreed = True
        if abs(float(a["brier"]) - float(b["brier"])) > 1e-6:
            disagreed = True
    assert disagreed, "report matches surface fixture; evaluation must not copy it"


def test_entrypoint_republish_is_byte_identical():
    """Require deterministic reports rebuilt through the documented entrypoint."""
    assert REPORT.is_file()
    original = REPORT.read_bytes()
    _republish(RERUN1)
    assert RERUN1.read_bytes() == original, "first republish differs from /output report"
    _republish(RERUN2)
    assert RERUN2.read_bytes() == original, "second republish differs from /output report"
    assert RERUN1.read_bytes() == RERUN2.read_bytes(), "consecutive republishes differ"
