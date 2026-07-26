"""Verifier tests for the speculative-decoding calibration report."""

import json
import subprocess
import tempfile

REPORT_PATH = "/output/recalibration-report.json"
BINARY_PATH = "/app/eng/target/release/spec-eval"
DATA_ROOT = "/app/data"
CRATE_ROOT = "/app/eng"
SCHEMA_TAG = "spec-calib-v1"
PROBE_SEED = "3405691582"
SLICES = ("num_completion", "repetition_prose", "low_entropy_json", "code_rare_tokens")


def _read_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.loads(fh.read())


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _assert_fixtures_intact() -> None:
    """Fixture integrity is anchored by /app/data/fixtures.sha256."""
    subprocess.run(
        ["bash", "/app/scripts/verify_fixtures.sh"],
        check=True,
        capture_output=True,
    )


def _load_report() -> dict:
    _assert_fixtures_intact()
    return _read_json(REPORT_PATH)


def _report_slice(report: dict, slice_id: str) -> dict:
    for entry in report["slices"]:
        if entry["slice_id"] == slice_id:
            return entry
    raise AssertionError(f"slice {slice_id} not present in report")


def _run_probe(slice_id: str, seed: str) -> list:
    _assert_fixtures_intact()
    fd, out = tempfile.mkstemp(suffix=".jsonl")
    import os as _os
    _os.close(fd)
    subprocess.run(
        [
            BINARY_PATH,
            "probe",
            "--slice",
            slice_id,
            "--data",
            DATA_ROOT,
            "--seed",
            seed,
            "--out",
            out,
        ],
        check=True,
        capture_output=True,
    )
    return [json.loads(line) for line in _read_text(out).splitlines() if line.strip()]


def _reference_counts(slice_id: str) -> dict:
    ref_path = f"{DATA_ROOT}/nonspec/{slice_id}.dat"
    counts: dict = {}
    for tok in _read_text(ref_path).split():
        counts[int(tok)] = counts.get(int(tok), 0) + 1
    return counts


def test_fixtures_untampered():
    """Fixture and config files match the checksums baked into fixtures.sha256."""
    _assert_fixtures_intact()


def test_report_schema_tag_and_slice_ids():
    """Report advertises the runner's schema tag and every expected slice."""
    report = _load_report()
    assert report.get("schema_tag") == SCHEMA_TAG
    slice_ids = {entry["slice_id"] for entry in report.get("slices", [])}
    assert slice_ids == set(SLICES)
    for entry in report["slices"]:
        assert isinstance(entry["positions"], int) and entry["positions"] > 0
        assert 0.0 <= float(entry["ks_statistic"]) <= 1.0
        assert 0.0 <= float(entry["accept_rate"]) <= 1.0
        assert 0.0 <= float(entry["divergence_rate"]) <= 1.0
        assert float(entry["speedup"]) >= 1.0
        assert 0.0 <= float(entry["fallback_rate"]) <= 1.0
        assert 0.0 <= float(entry["low_entropy_accept_rate"]) <= 1.0
        assert 0.0 <= float(entry["high_entropy_accept_rate"]) <= 1.0
        assert 0.0 <= float(entry["mean_draft_target_tv"]) <= 1.0


def test_report_summary_block_populated():
    """Summary block reports pooled speedup, divergence, and fallback rate."""
    report = _load_report()
    summary = report["summary"]
    assert float(summary["overall_speedup"]) >= 1.0
    assert 0.0 <= float(summary["overall_divergence"]) <= 1.0
    assert 0.0 <= float(summary["overall_fallback_rate"]) <= 1.0


def test_ks_within_per_slice_budget():
    """Every slice's KS distance from the reference sits at or below the tolerance."""
    report = _load_report()
    for slice_id in SLICES:
        entry = _report_slice(report, slice_id)
        assert float(entry["ks_statistic"]) <= 0.10, (slice_id, entry["ks_statistic"])


def test_per_slice_acceptance_floor():
    """Every slice preserves an acceptance rate well above the naive floor."""
    report = _load_report()
    for slice_id in SLICES:
        entry = _report_slice(report, slice_id)
        assert float(entry["accept_rate"]) >= 0.75, (slice_id, entry["accept_rate"])


def test_per_slice_divergence_budget():
    """Emitted token stream stays within a small divergence budget on every slice."""
    report = _load_report()
    for slice_id in SLICES:
        entry = _report_slice(report, slice_id)
        assert float(entry["divergence_rate"]) <= 0.10, (slice_id, entry["divergence_rate"])


def test_overall_speedup_preserved():
    """Pooled speedup stays within the documented health band."""
    report = _load_report()
    spd = float(report["summary"]["overall_speedup"])
    assert spd >= 1.60, spd
    assert spd < 2.0, spd


def test_overall_divergence_pooled_bound():
    """Pooled divergence across every emitted position is small."""
    report = _load_report()
    assert float(report["summary"]["overall_divergence"]) <= 0.075


def test_no_trivial_low_entropy_bypass():
    """High-entropy positions keep an acceptance rate close to the ceiling and overall fallback is bounded."""
    report = _load_report()
    high = report["positions"]["high_entropy"]
    assert int(high["count"]) > 0
    assert float(high["accept_rate"]) >= 0.85, high
    assert float(report["summary"]["overall_fallback_rate"]) <= 0.20
    for slice_id in SLICES:
        entry = _report_slice(report, slice_id)
        assert float(entry["high_entropy_accept_rate"]) >= 0.80, (slice_id, entry)
        assert float(entry["fallback_rate"]) <= 0.15, (slice_id, entry["fallback_rate"])


def test_low_entropy_accept_rate_preserved():
    """Low-entropy positions keep an acceptance rate close to the ceiling, matching the public contract."""
    report = _load_report()
    low = report["positions"]["low_entropy"]
    assert int(low["count"]) > 0
    assert float(low["accept_rate"]) >= 0.85, low


def test_no_perfect_draft_or_target_copy():
    """Draft must remain distinct from target; perfect-draft / target-copy shortcuts fail."""
    report = _load_report()
    # Exact target-copy yields accept_rate == 1 and mean_draft_target_tv == 0.
    overall_accept = float(report["summary"]["overall_speedup"]) - 1.0
    assert overall_accept < 1.0, report["summary"]
    for slice_id in SLICES:
        entry = _report_slice(report, slice_id)
        tv = float(entry["mean_draft_target_tv"])
        assert tv >= 0.003, (slice_id, tv)
        assert tv <= 0.06, (slice_id, tv)


def test_slice_specific_num_completion_and_json_tight():
    """Numeric-completion and low-entropy-JSON slices meet a tighter KS bound."""
    report = _load_report()
    num = _report_slice(report, "num_completion")
    js = _report_slice(report, "low_entropy_json")
    assert float(num["ks_statistic"]) <= 0.05
    assert float(js["ks_statistic"]) <= 0.05
    assert float(num["divergence_rate"]) <= 0.05
    assert float(js["divergence_rate"]) <= 0.05


def test_slice_specific_code_rare_tokens():
    """Code-with-rare-tokens slice meets both KS and divergence budgets."""
    report = _load_report()
    entry = _report_slice(report, "code_rare_tokens")
    assert float(entry["ks_statistic"]) <= 0.08
    assert float(entry["divergence_rate"]) <= 0.08
    assert float(entry["accept_rate"]) >= 0.80


def test_probe_reconstruction_matches_report():
    """Per-position probe events reconstruct the same metrics as the report."""
    report = _load_report()
    for slice_id in SLICES:
        events = _run_probe(slice_id, PROBE_SEED)
        total = len(events)
        assert total > 0
        accepts = sum(int(ev["accepted"]) for ev in events)
        fallbacks = sum(int(ev["fallback"]) for ev in events)
        diverges = sum(1 for ev in events if int(ev["emitted"]) != int(ev["reference"]))
        mean_tv = sum(float(ev["draft_target_tv"]) for ev in events) / total

        entry = _report_slice(report, slice_id)
        assert abs(accepts / total - float(entry["accept_rate"])) < 1e-6, slice_id
        assert abs(fallbacks / total - float(entry["fallback_rate"])) < 1e-6, slice_id
        assert abs(diverges / total - float(entry["divergence_rate"])) < 1e-6, slice_id
        assert abs(mean_tv - float(entry["mean_draft_target_tv"])) < 1e-6, slice_id


def test_probe_matches_reference_distribution():
    """Emitted token histogram (from probe) matches the on-disk reference bucket."""
    for slice_id in SLICES:
        events = _run_probe(slice_id, PROBE_SEED)
        emitted = [int(ev["emitted"]) for ev in events]
        ref_counts = _reference_counts(slice_id)
        emitted_counts: dict = {}
        for tok in emitted:
            emitted_counts[tok] = emitted_counts.get(tok, 0) + 1
        tv = 0.0
        vocab = set(ref_counts) | set(emitted_counts)
        e_total = max(len(emitted), 1)
        r_total = max(sum(ref_counts.values()), 1)
        for token in vocab:
            e = emitted_counts.get(token, 0) / e_total
            r = ref_counts.get(token, 0) / r_total
            tv += abs(e - r)
        assert 0.5 * tv <= 0.20, (slice_id, tv)


def test_engine_rebuilds_and_matches_gold():
    """Fresh rebuild from source produces the same metrics as the shipped report."""
    _assert_fixtures_intact()
    result = subprocess.run(
        ["cargo", "build", "--release", "--offline", "--locked"],
        cwd=CRATE_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    fd, fresh_out = tempfile.mkstemp(suffix=".json")
    import os as _os
    _os.close(fd)
    subprocess.run(
        [BINARY_PATH, "eval", "--data", DATA_ROOT, "--seed", PROBE_SEED, "--out", fresh_out],
        check=True,
        capture_output=True,
    )
    gold = _read_json(REPORT_PATH)
    fresh = _read_json(fresh_out)
    assert fresh["schema_tag"] == gold["schema_tag"] == SCHEMA_TAG
    for slice_id in SLICES:
        g = _report_slice(gold, slice_id)
        f = _report_slice(fresh, slice_id)
        for field in ("ks_statistic", "accept_rate", "divergence_rate",
                      "fallback_rate", "low_entropy_accept_rate",
                      "high_entropy_accept_rate", "mean_draft_target_tv"):
            assert abs(float(g[field]) - float(f[field])) < 1e-9, (slice_id, field, g[field], f[field])
    for bucket in ("low_entropy", "high_entropy"):
        for field in ("count", "accept_rate", "fallback_rate"):
            gv = float(gold["positions"][bucket][field])
            fv = float(fresh["positions"][bucket][field])
            assert abs(gv - fv) < 1e-9, (bucket, field, gv, fv)
    for field in ("overall_speedup", "overall_divergence", "overall_fallback_rate"):
        gv = float(gold["summary"][field])
        fv = float(fresh["summary"][field])
        assert abs(gv - fv) < 1e-9, ("summary", field, gv, fv)


def test_config_tables_present():
    """All four calibration knob JSON tables exist under /app/data/config."""
    for name in ("layer_scales", "quant_blocks", "codebook_stats", "params"):
        path = f"{DATA_ROOT}/config/{name}.json"
        data = json.loads(_read_text(path))
        assert isinstance(data, dict) and data


def test_probe_events_have_required_fields():
    """Every probe event carries the fields documented in metrics.md."""
    required = {
        "slice",
        "pos",
        "emitted",
        "reference",
        "accepted",
        "fallback",
        "entropy",
        "rare_flag",
        "draft_target_tv",
    }
    events = _run_probe("code_rare_tokens", PROBE_SEED)
    assert events, "code_rare_tokens probe returned zero events"
    for ev in events:
        assert required.issubset(ev.keys()), (required - ev.keys())
        assert isinstance(ev["pos"], int)
        assert isinstance(ev["emitted"], int)
        assert isinstance(ev["reference"], int)
        assert ev["accepted"] in (0, 1)
        assert ev["fallback"] in (0, 1)
        assert 0.0 <= float(ev["draft_target_tv"]) <= 1.0
