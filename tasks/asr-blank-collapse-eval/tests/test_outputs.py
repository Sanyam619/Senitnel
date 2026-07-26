"""Verifier for asr-blank-collapse-eval.

Grades /output/asr-eval.json against the published bands, the exact metric
values a faithful pass produces on the frozen posteriors, the bound decoder
registry generation, the entrypoint republish after a workspace rebuild, and a
novel sealed generation inject.
"""

import json
import subprocess
from pathlib import Path

REPORT = Path("/output/asr-eval.json")
ENTRY = "/app/scripts/run_asr_eval.sh"
PIN = Path(__file__).resolve().parent / "data.sha256"
STAGE = Path("/logs/verifier")
JOURNAL = Path("/app/data/decoder_registry/tip_journal.jsonl")
SELECTION = Path("/app/calib/decoder_selection.txt")
SWEEP = Path("/app/data/fixtures/probe_ok.json")

IDS = ("read_a", "read_b", "spont_a", "spont_b", "far_c", "far_d")

SCHEMA_TAG = "asr-eval-v3"
ROUTE_EXPECTED = "ctc_collapse"
EPOCH_EXPECTED = 6
WEIGHT_EXPECTED = 0.35
WEIGHT_TOL = 1e-6
METRIC_TOL = 1e-6
COPY_GAP = 1e-4
GUARD = 0.04

# Generations that are present in the journal but must not be bound: 9 is the
# newest sealed row and was withdrawn, 3/7/11 are staging rows.
RETIRED_ROW = 9
LIVE_ROWS = (3, 7, 11)

EXPECTED = {
    "read_a": (0.028985507246, 0.022900763359),
    "read_b": (0.043478260870, 0.035156250000),
    "spont_a": (0.066666666667, 0.054744525547),
    "spont_b": (0.109589041096, 0.083333333333),
    "far_c": (0.095890410959, 0.070110701107),
    "far_d": (0.191780821918, 0.136531365314),
}

BANDS = {
    "read_a": (0.009, 0.049, 0.007, 0.039),
    "read_b": (0.023, 0.063, 0.019, 0.051),
    "spont_a": (0.047, 0.087, 0.039, 0.071),
    "spont_b": (0.090, 0.130, 0.067, 0.099),
    "far_c": (0.076, 0.116, 0.054, 0.086),
    "far_d": (0.172, 0.212, 0.121, 0.153),
}

NOVEL_ROW = {
    "idx": 13,
    "state": "sealed",
    "tip": "tip_r13",
    "sheet": "k9",
    "mode": "rnnt_join",
}
NOVEL_WEIGHT = 0.44
NOVEL_FLOOR = 0.28

_CACHE = {}


def _finite(v):
    return float("-inf") < float(v) < float("inf")


def _entry():
    STAGE.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["/bin/bash", ENTRY],
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    assert proc.returncode == 0, f"entrypoint failed:\n{proc.stdout}\n{proc.stderr}"
    assert REPORT.is_file(), "entrypoint did not publish /output/asr-eval.json"
    return REPORT.read_bytes()


def _published():
    """The report as the agent left it, captured before any republish."""
    if "published" not in _CACHE:
        assert REPORT.is_file(), "missing /output/asr-eval.json"
        raw = REPORT.read_bytes()
        STAGE.mkdir(parents=True, exist_ok=True)
        (STAGE / "asr-eval-published.json").write_bytes(raw)
        _CACHE["published_raw"] = raw
        _CACHE["published"] = json.loads(raw.decode("utf-8"))
    return _CACHE["published"]


def _rebuilt():
    """The report the entrypoint publishes after rebuilding the workspace."""
    if "rebuilt" not in _CACHE:
        _published()
        raw = _entry()
        (STAGE / "asr-eval-rerun1.json").write_bytes(raw)
        _CACHE["rebuilt_raw"] = raw
        _CACHE["rebuilt"] = json.loads(raw.decode("utf-8"))
    return _CACHE["rebuilt"]


def _slices(doc):
    rows = doc.get("slices")
    assert isinstance(rows, list), "slices must be an array"
    got = [r.get("id") for r in rows]
    assert got == list(IDS), f"slice ids/order mismatch: {got}"
    return {r["id"]: r for r in rows}


def _sweep_rows():
    doc = json.loads(SWEEP.read_text(encoding="utf-8"))
    return {r["id"]: r for r in doc["slices"]}


def test_frozen_inputs_integrity():
    """Posteriors, alignments, lexicon, conditioning and prediction tables,
    fusion sheets, decoder registry, and the published bands doc must keep
    their shipped SHA-256 digests, and a report must have been published from
    them."""
    assert REPORT.is_file(), "missing /output/asr-eval.json"
    proc = subprocess.run(
        ["sha256sum", "-c", str(PIN)],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert proc.returncode == 0, (
        f"frozen evaluation inputs were modified:\n{proc.stdout}\n{proc.stderr}"
    )


def test_report_schema_and_slice_order():
    """Report carries the asr-eval-v3 tag, the six slice ids in the published
    order, numeric rates in range, a string decode path, a numeric fusion
    weight, and an integer generation."""
    doc = _published()
    assert doc.get("schema_tag") == SCHEMA_TAG, "schema_tag mismatch"
    assert isinstance(doc.get("eval_ok"), bool), "eval_ok must be a boolean"
    rows = _slices(doc)
    for sid in IDS:
        row = rows[sid]
        for key in ("wer", "cer"):
            v = row.get(key)
            assert isinstance(v, (int, float)) and not isinstance(v, bool), (
                f"{sid}.{key} must be a number"
            )
            assert _finite(v), f"{sid}.{key} must be finite"
            assert 0.0 <= float(v) <= 1.0, f"{sid}.{key} out of range"
        assert isinstance(row.get("blank_mode"), str), f"{sid}.blank_mode must be a string"
        w = row.get("lm_weight")
        assert isinstance(w, (int, float)) and not isinstance(w, bool), (
            f"{sid}.lm_weight must be a number"
        )
        assert _finite(w), f"{sid}.lm_weight must be finite"
        e = row.get("tip_epoch")
        assert isinstance(e, int) and not isinstance(e, bool), (
            f"{sid}.tip_epoch must be an integer"
        )


def _assert_configuration_owns_the_rates(rows):
    """A reported configuration only describes the run when the rates beside it
    are in the neighbourhood the bands were measured in."""
    for sid in IDS:
        wer = float(rows[sid]["wer"])
        cer = float(rows[sid]["cer"])
        lo_w, hi_w, lo_c, hi_c = BANDS[sid]
        assert lo_w - GUARD <= wer <= hi_w + GUARD, (
            f"{sid}.wer {wer} could not have come from the reported configuration"
        )
        assert lo_c - GUARD <= cer <= hi_c + GUARD, (
            f"{sid}.cer {cer} could not have come from the reported configuration"
        )


def test_blank_mode_is_bound_decoder_path():
    """Every slice reports the decode path the bound generation was sealed
    with, and the rates beside it come from that path."""
    rows = _slices(_rebuilt())
    for sid in IDS:
        got = rows[sid]["blank_mode"]
        assert got == ROUTE_EXPECTED, (
            f"{sid}.blank_mode {got!r} is not the bound generation's decode path"
        )
    _assert_configuration_owns_the_rates(rows)


def test_tip_epoch_is_bound_registry_generation():
    """tip_epoch is the decoder registry generation the desk binds, and the
    rates beside it come from a pass under that generation."""
    rows = _slices(_rebuilt())
    for sid in IDS:
        got = rows[sid]["tip_epoch"]
        assert got == EPOCH_EXPECTED, (
            f"{sid}.tip_epoch {got} is not the bound registry generation"
        )
    _assert_configuration_owns_the_rates(rows)


def test_tip_epoch_is_not_withdrawn_or_staging_row():
    """The withdrawn sealed row and the staging rows must not be bound."""
    rows = _slices(_rebuilt())
    for sid in IDS:
        got = rows[sid]["tip_epoch"]
        assert got != RETIRED_ROW, f"{sid}.tip_epoch binds the withdrawn generation"
        assert got not in LIVE_ROWS, f"{sid}.tip_epoch binds a staging generation"
    _assert_configuration_owns_the_rates(rows)


def test_lm_weight_is_bound_generation_fusion_row():
    """The reported shallow-fusion weight is the row the bound generation
    resolves on its own sheet, and the rates beside it come from searching
    under that weight."""
    rows = _slices(_rebuilt())
    for sid in IDS:
        got = float(rows[sid]["lm_weight"])
        assert abs(got - WEIGHT_EXPECTED) <= WEIGHT_TOL, (
            f"{sid}.lm_weight {got} is not the bound generation's fusion row"
        )
    _assert_configuration_owns_the_rates(rows)


def _assert_rates(sids):
    rows = _slices(_rebuilt())
    for sid in sids:
        wer = float(rows[sid]["wer"])
        cer = float(rows[sid]["cer"])
        want_w, want_c = EXPECTED[sid]
        assert abs(wer - want_w) <= METRIC_TOL, (
            f"{sid}.wer {wer} does not match a faithful pass ({want_w})"
        )
        assert abs(cer - want_c) <= METRIC_TOL, (
            f"{sid}.cer {cer} does not match a faithful pass ({want_c})"
        )


def test_read_slices_match_faithful_pass():
    """Read-speech slices carry the rates a faithful pass produces on the
    frozen posteriors."""
    _assert_rates(("read_a", "read_b"))


def test_spontaneous_slices_match_faithful_pass():
    """Spontaneous-speech slices carry the rates a faithful pass produces on
    the frozen posteriors."""
    _assert_rates(("spont_a", "spont_b"))


def test_far_field_slices_match_faithful_pass():
    """Far-field slices carry the rates a faithful pass produces on the frozen
    posteriors."""
    _assert_rates(("far_c", "far_d"))


def test_all_slices_inside_published_bands():
    """Every published slice lands inside both bands and eval_ok is true."""
    doc = _rebuilt()
    rows = _slices(doc)
    for sid in IDS:
        wer = float(rows[sid]["wer"])
        cer = float(rows[sid]["cer"])
        lo_w, hi_w, lo_c, hi_c = BANDS[sid]
        assert lo_w <= wer <= hi_w, f"{sid}.wer {wer} outside published band"
        assert lo_c <= cer <= hi_c, f"{sid}.cer {cer} outside published band"
    assert doc.get("eval_ok") is True, "eval_ok is not true"


def test_published_rates_are_not_the_captured_sweep():
    """Rates must come from decoding the frozen posteriors, not from the
    captured sweep fixture."""
    rows = _slices(_rebuilt())
    sweep = _sweep_rows()
    for sid in IDS:
        if sid not in sweep:
            continue
        dw = abs(float(rows[sid]["wer"]) - float(sweep[sid]["wer"]))
        dc = abs(float(rows[sid]["cer"]) - float(sweep[sid]["cer"]))
        assert dw > COPY_GAP or dc > COPY_GAP, (
            f"{sid} rates were copied from the captured sweep"
        )


def test_entrypoint_republish_is_byte_identical():
    """The report the agent published must equal what the entrypoint publishes
    after rebuilding the workspace, and a second republish must match too."""
    first = _rebuilt()
    assert first is not None
    assert _CACHE["published_raw"] == _CACHE["rebuilt_raw"], (
        "published report differs from the report the rebuilt workspace emits"
    )
    again = _entry()
    (STAGE / "asr-eval-rerun2.json").write_bytes(again)
    assert again == _CACHE["rebuilt_raw"], "two consecutive republishes differ"


def test_novel_sealed_generation_moves_the_report():
    """A sealed generation the desk has never seen must move the bound
    generation, decode path, fusion weight, and every rate together."""
    base = _slices(_rebuilt())
    journal = JOURNAL.read_bytes()
    selection = SELECTION.read_bytes()
    try:
        with JOURNAL.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(NOVEL_ROW) + "\n")
        SELECTION.write_text(
            f"selected_tip = {NOVEL_ROW['tip']}\n"
            f"selected_generation = {NOVEL_ROW['idx']}\n",
            encoding="utf-8",
        )
        raw = _entry()
        (STAGE / "asr-eval-novel.json").write_bytes(raw)
        doc = json.loads(raw.decode("utf-8"))
        rows = _slices(doc)
        for sid in IDS:
            row = rows[sid]
            assert row["tip_epoch"] == NOVEL_ROW["idx"], (
                f"{sid}.tip_epoch did not move to the novel sealed generation"
            )
            assert row["blank_mode"] == NOVEL_ROW["mode"], (
                f"{sid}.blank_mode did not move to the novel generation's path"
            )
            assert abs(float(row["lm_weight"]) - NOVEL_WEIGHT) <= WEIGHT_TOL, (
                f"{sid}.lm_weight did not resolve the novel generation's row"
            )
            wer = float(row["wer"])
            assert wer > NOVEL_FLOOR, (
                f"{sid}.wer {wer} is not a joined pass conditioned on the "
                "prediction state"
            )
            assert wer <= 1.0, f"{sid}.wer {wer} out of range"
            assert abs(wer - float(base[sid]["wer"])) > COPY_GAP, (
                f"{sid}.wer did not move with the novel sealed generation"
            )
        assert doc.get("eval_ok") is False, (
            "eval_ok claims the novel generation lands inside the bands"
        )
    finally:
        JOURNAL.write_bytes(journal)
        SELECTION.write_bytes(selection)
        _entry()
