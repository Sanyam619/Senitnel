"""Verifier for int4-weight-only-calibration-eval.

Grades /output/int4-eval.json against the published bands, the exact numbers a
faithful four-bit weight-only pass produces on the frozen snapshots, the
grouping width and number of the generation the registry resolves, cold/resume
parity, the calibration window the scale sheet is measured over, the entrypoint
republish after a workspace rebuild, and a novel sealed grouped generation.
"""

import json
import subprocess
from pathlib import Path

REPORT = Path("/output/int4-eval.json")
ENTRY = "/app/scripts/run_int4_eval.sh"
PIN = Path(__file__).resolve().parent / "data.sha256"
STAGE = Path("/logs/verifier")
JOURNAL = Path("/app/data/quant_registry/tip_journal.jsonl")
GRIDS = Path("/app/data/quant_grids")
RECEIPT = Path("/app/serving/bind.accept")
LEDGER = Path("/app/data/calib/admit_ledger.jsonl")
CALIB = Path("/app/data/calib")
SCALES = Path("/app/data/scales")
SWEEP = Path("/app/data/fixtures/surface_ok.json")

IDS = ("cold_a", "resume_a", "cold_b", "resume_b", "mix_c", "mix_d")
PAIRS = (("cold_a", "resume_a"), ("cold_b", "resume_b"))

SCHEMA_TAG = "int4-eval-v1"
NUM_TOL = 2e-9
PAIR_TOL = 1e-4
COPY_GAP = 1e-4
GUARD = 0.06

GROUP_EXPECTED = 8
EPOCH_EXPECTED = 7

# 32 is the live sheet and the sealed per-channel sheet; 4 is the rolled-back
# generation and the two older sealed sheets; 2 is the staged sheet.
REJECTED_WIDTHS = (2, 4, 32)
ROLLED_BACK_EPOCH = 9
NOT_SCORING_EPOCHS = (2, 4, 5, 6, 11, 12)

PPL_EXPECTED = {
    "cold_a": 1.4768763357097023,
    "resume_a": 1.4768763357097023,
    "cold_b": 1.4572031163351050,
    "resume_b": 1.4572031163351050,
    "mix_c": 1.5812775129334236,
    "mix_d": 1.4251431132692813,
}
TOP1_EXPECTED = {
    "cold_a": 0.89375,
    "resume_a": 0.89375,
    "cold_b": 0.88125,
    "resume_b": 0.88125,
    "mix_c": 0.84375,
    "mix_d": 0.86875,
}
BANDS = {
    "cold_a": (1.41, 1.54),
    "resume_a": (1.41, 1.54),
    "cold_b": (1.39, 1.52),
    "resume_b": (1.39, 1.52),
    "mix_c": (1.51, 1.65),
    "mix_d": (1.36, 1.49),
}
TOP1_BANDS = {
    "cold_a": (0.869, 0.919),
    "resume_a": (0.869, 0.919),
    "cold_b": (0.856, 0.906),
    "resume_b": (0.856, 0.906),
    "mix_c": (0.819, 0.869),
    "mix_d": (0.844, 0.894),
}

# A pass whose calibration window has been widened to admit the third shard.
WIDENED_SHARD = "shard_c"
WIDENED_PPL = {
    "cold_a": 1.3765468834861092,
    "resume_a": 1.3765468834861092,
    "cold_b": 1.5154585985773537,
    "resume_b": 1.5154585985773537,
    "mix_c": 1.5941062304349290,
    "mix_d": 1.5084681651024456,
}

NOVEL_TIP = "tip_n13"
NOVEL_EPOCH = 13
NOVEL_GROUP = 4
NOVEL_GROUPS = 22

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
    assert REPORT.is_file(), "entrypoint did not publish /output/int4-eval.json"
    return REPORT.read_bytes()


def _published():
    """The report as the agent left it, captured before any republish."""
    if "published" not in _CACHE:
        assert REPORT.is_file(), "missing /output/int4-eval.json"
        raw = REPORT.read_bytes()
        STAGE.mkdir(parents=True, exist_ok=True)
        (STAGE / "int4-eval-published.json").write_bytes(raw)
        _CACHE["published_raw"] = raw
        _CACHE["published"] = json.loads(raw.decode("utf-8"))
    return _CACHE["published"]


def _rebuilt():
    """The report the entrypoint publishes after rebuilding the workspace."""
    if "rebuilt" not in _CACHE:
        _published()
        raw = _entry()
        (STAGE / "int4-eval-rerun1.json").write_bytes(raw)
        _CACHE["rebuilt_raw"] = raw
        _CACHE["rebuilt"] = json.loads(raw.decode("utf-8"))
    return _CACHE["rebuilt"]


def _rows(doc):
    cells = doc.get("scenarios")
    assert isinstance(cells, list), "scenarios must be an array"
    got = [c.get("id") for c in cells]
    assert got == list(IDS), f"scenario ids/order mismatch: {got}"
    return {c["id"]: c for c in cells}


def _republish(tag):
    raw = _entry()
    (STAGE / f"int4-eval-{tag}.json").write_bytes(raw)
    return _rows(json.loads(raw.decode("utf-8"))), json.loads(raw.decode("utf-8"))


def _assert_metric_owns_the_row(rows):
    """A reported width and generation only describe the run when the
    perplexity beside them is in the neighbourhood the bands were measured
    in."""
    for sid in IDS:
        ppl = float(rows[sid]["perplexity"])
        lo, hi = BANDS[sid]
        assert lo - GUARD <= ppl <= hi + GUARD, (
            f"{sid}.perplexity {ppl} could not have come from the reported generation"
        )


def _assert_metrics(sids, table=None):
    rows = _rows(_rebuilt())
    want = table or PPL_EXPECTED
    for sid in sids:
        ppl = float(rows[sid]["perplexity"])
        assert abs(ppl - want[sid]) <= NUM_TOL, (
            f"{sid}.perplexity {ppl} does not match a faithful pass ({want[sid]})"
        )
        top1 = float(rows[sid]["top1"])
        assert abs(top1 - TOP1_EXPECTED[sid]) <= NUM_TOL, (
            f"{sid}.top1 {top1} does not match a faithful pass ({TOP1_EXPECTED[sid]})"
        )


def test_frozen_inputs_integrity():
    """The layer layout, the FP16 snapshots, the grouping sheets, the registry,
    the captured banks, the calibration rows, the evaluation slices and the
    published bands must keep their shipped SHA-256 digests, and a report must
    have been published from them."""
    assert REPORT.is_file(), "missing /output/int4-eval.json"
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


def test_report_schema_and_scenario_order():
    """Report carries the int4-eval-v1 tag, the six scenario ids in roster
    order, numeric perplexity and top-1 in range, and integer grouping width
    and generation number."""
    doc = _published()
    assert doc.get("schema_tag") == SCHEMA_TAG, "schema_tag mismatch"
    assert isinstance(doc.get("bands_ok"), bool), "bands_ok must be a boolean"
    rows = _rows(doc)
    for sid in IDS:
        row = rows[sid]
        ppl = row.get("perplexity")
        assert isinstance(ppl, (int, float)) and not isinstance(ppl, bool), (
            f"{sid}.perplexity must be a number"
        )
        assert _finite(ppl) and float(ppl) >= 1.0, f"{sid}.perplexity out of range"
        top1 = row.get("top1")
        assert isinstance(top1, (int, float)) and not isinstance(top1, bool), (
            f"{sid}.top1 must be a number"
        )
        assert 0.0 <= float(top1) <= 1.0, f"{sid}.top1 out of range"
        for key in ("group_size", "tip_epoch"):
            v = row.get(key)
            assert isinstance(v, int) and not isinstance(v, bool), (
                f"{sid}.{key} must be an integer"
            )
            assert v > 0, f"{sid}.{key} out of range"


def test_group_size_is_the_resolved_grouped_generation():
    """Every scenario reports the grouping width of the generation the registry
    resolves, and the perplexity beside it comes from a pass at that width."""
    rows = _rows(_rebuilt())
    for sid in IDS:
        got = rows[sid]["group_size"]
        assert got == GROUP_EXPECTED, (
            f"{sid}.group_size {got} is not the resolved generation's grouping width"
        )
    _assert_metric_owns_the_row(rows)


def test_group_size_is_not_the_live_or_rolled_back_sheet():
    """The live per-channel sheet, the sealed per-channel sheet, the rolled-back
    generation and the staged sheets must not set the reported width."""
    rows = _rows(_rebuilt())
    for sid in IDS:
        got = rows[sid]["group_size"]
        assert got not in REJECTED_WIDTHS, (
            f"{sid}.group_size {got} comes from a sheet the desk does not score under"
        )
    _assert_metric_owns_the_row(rows)


def test_tip_epoch_is_the_sealed_scale_bank_generation():
    """Every scenario reports the number of the sealed grouped generation that
    has not been rolled back."""
    rows = _rows(_rebuilt())
    for sid in IDS:
        got = rows[sid]["tip_epoch"]
        assert got == EPOCH_EXPECTED, (
            f"{sid}.tip_epoch {got} is not the resolved generation"
        )
        assert got != ROLLED_BACK_EPOCH, f"{sid}.tip_epoch scores a rolled-back generation"
        assert got not in NOT_SCORING_EPOCHS, (
            f"{sid}.tip_epoch scores a generation the desk does not score under"
        )
    _assert_metric_owns_the_row(rows)


def test_first_domain_scenarios_match_faithful_pass():
    """The scenarios scored on the first input domain carry the perplexity and
    top-1 a faithful pass produces on the frozen snapshots."""
    _assert_metrics(("cold_a", "resume_a"))


def test_second_domain_scenarios_match_faithful_pass():
    """The scenarios scored on the second input domain carry the perplexity and
    top-1 a faithful pass produces on the frozen snapshots."""
    _assert_metrics(("cold_b", "resume_b"))


def test_mixed_domain_scenarios_match_faithful_pass():
    """The mixed-domain scenarios carry the perplexity and top-1 a faithful
    pass produces on the frozen snapshots."""
    _assert_metrics(("mix_c", "mix_d"))


def test_cold_and_resume_partners_agree():
    """A cold scenario and its resume partner are one measurement taken from
    two starting points, so their perplexity and top-1 agree to within 1e-4."""
    rows = _rows(_rebuilt())
    for cold, resume in PAIRS:
        for key in ("perplexity", "top1"):
            left = float(rows[cold][key])
            right = float(rows[resume][key])
            assert abs(left - right) <= PAIR_TOL, (
                f"{cold}/{resume} {key} {left}/{right} do not reproduce each other"
            )
    _assert_metric_owns_the_row(rows)


def test_all_scenarios_inside_published_bands():
    """Every published scenario lands inside its perplexity band and its top-1
    band, and bands_ok is true."""
    doc = _rebuilt()
    rows = _rows(doc)
    for sid in IDS:
        ppl = float(rows[sid]["perplexity"])
        lo, hi = BANDS[sid]
        assert lo <= ppl <= hi, f"{sid}.perplexity {ppl} outside published band"
        top1 = float(rows[sid]["top1"])
        tlo, thi = TOP1_BANDS[sid]
        assert tlo <= top1 <= thi, f"{sid}.top1 {top1} outside published band"
    assert doc.get("bands_ok") is True, "bands_ok is not true"


def test_published_numbers_are_not_the_captured_sweep():
    """Numbers must come from quantizing and scoring the frozen snapshots, not
    from the captured sweep fixture."""
    rows = _rows(_rebuilt())
    sweep = {r["id"]: r for r in json.loads(SWEEP.read_text(encoding="utf-8"))["scenarios"]}
    for sid in IDS:
        if sid not in sweep:
            continue
        moved = abs(float(rows[sid]["perplexity"]) - float(sweep[sid]["perplexity"]))
        assert moved > COPY_GAP, f"{sid} perplexity was copied from the captured sweep"
        assert rows[sid]["group_size"] != sweep[sid]["group_size"], (
            f"{sid} reports the captured sweep's grouping width"
        )


def test_entrypoint_republish_is_byte_identical():
    """The report the agent published must equal what the entrypoint publishes
    after rebuilding the workspace, and a second republish must match too."""
    assert _rebuilt() is not None
    assert _CACHE["published_raw"] == _CACHE["rebuilt_raw"], (
        "published report differs from the report the rebuilt workspace emits"
    )
    again = _entry()
    (STAGE / "int4-eval-rerun2.json").write_bytes(again)
    assert again == _CACHE["rebuilt_raw"], "two consecutive republishes differ"


def test_scales_do_not_come_from_the_captured_banks():
    """The captured bank the registry names for the resolved generation is a
    stored capture, so moving it must not move the report."""
    assert _rebuilt() is not None
    bank = SCALES / "bank_g7.txt"
    keep = bank.read_bytes()
    try:
        lines = keep.decode("utf-8").splitlines()
        for at, line in enumerate(lines):
            cols = line.split()
            if cols and cols[0] == "gain":
                lines[at] = " ".join(cols[:2] + [repr(float(c) * 1.7 + 0.25) for c in cols[2:]])
        bank.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
        raw = _entry()
        (STAGE / "int4-eval-bank.json").write_bytes(raw)
        assert raw == _CACHE["rebuilt_raw"], (
            "the report follows a captured scale bank instead of a measured scale sheet"
        )
    finally:
        bank.write_bytes(keep)
        _entry()


def test_unadmitted_calibration_rows_do_not_reach_the_scales():
    """A shard whose admission window does not cover the resolved generation is
    not part of the pass, so moving its rows must not move the report."""
    assert _rebuilt() is not None
    shard = CALIB / "shard_c.txt"
    keep = shard.read_bytes()
    try:
        lines = keep.decode("utf-8").splitlines()
        for at, line in enumerate(lines):
            cols = line.split()
            if cols and cols[0] == "row":
                lines[at] = "row " + " ".join(repr(float(c) * 2.3 - 0.4) for c in cols[1:])
        shard.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
        raw = _entry()
        (STAGE / "int4-eval-unadmitted.json").write_bytes(raw)
        assert raw == _CACHE["rebuilt_raw"], (
            "rows outside the admitted calibration window reached the scale sheet"
        )
    finally:
        shard.write_bytes(keep)
        _entry()


def test_admitted_calibration_rows_reach_the_scales():
    """The scale sheet is measured on the admitted calibration rows, so moving
    one of those shards must move every scenario while the partners keep
    reproducing each other."""
    base = _rows(_rebuilt())
    shard = CALIB / "shard_b.txt"
    keep = shard.read_bytes()
    try:
        lines = keep.decode("utf-8").splitlines()
        for at, line in enumerate(lines):
            cols = line.split()
            if cols and cols[0] == "row":
                lines[at] = "row " + " ".join(repr(float(c) * 1.9 + 0.35) for c in cols[1:])
        shard.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
        rows, _doc = _republish("admitted")
        for sid in IDS:
            moved = abs(float(rows[sid]["perplexity"]) - float(base[sid]["perplexity"]))
            assert moved > COPY_GAP, (
                f"{sid} did not move when the admitted calibration rows moved"
            )
        for cold, resume in PAIRS:
            left = float(rows[cold]["perplexity"])
            right = float(rows[resume]["perplexity"])
            assert abs(left - right) <= PAIR_TOL, (
                f"{cold}/{resume} stopped reproducing each other"
            )
    finally:
        shard.write_bytes(keep)
        _entry()


def test_scales_track_the_admitted_calibration_window():
    """Widening a shard's admission window so it covers the resolved generation
    folds that shard into the pass and moves every scenario onto the numbers
    that window produces."""
    assert _rebuilt() is not None
    keep = LEDGER.read_bytes()
    try:
        notes = []
        for line in keep.decode("utf-8").splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            row = json.loads(line)
            if row["shard"] == WIDENED_SHARD:
                row["last"] = 20
            notes.append(json.dumps(row))
        LEDGER.write_bytes(("\n".join(notes) + "\n").encode("utf-8"))
        rows, _doc = _republish("widened")
        for sid in IDS:
            ppl = float(rows[sid]["perplexity"])
            assert abs(ppl - WIDENED_PPL[sid]) <= NUM_TOL, (
                f"{sid}.perplexity {ppl} is not the widened calibration window's number"
            )
        for cold, resume in PAIRS:
            assert abs(float(rows[cold]["perplexity"]) - float(rows[resume]["perplexity"])) <= (
                PAIR_TOL
            ), f"{cold}/{resume} stopped reproducing each other under the widened window"
    finally:
        LEDGER.write_bytes(keep)
        _entry()


def test_novel_sealed_generation_moves_the_report():
    """A sealed grouped generation the desk has never seen must move the
    grouping width, the generation number and every metric together, and must
    leave the published bands."""
    base = _rows(_rebuilt())
    journal = JOURNAL.read_bytes()
    receipt = RECEIPT.read_bytes()
    sheet = GRIDS / "grid_n13.txt"
    try:
        sheet.write_text(
            "\n".join(
                [
                    f"tip {NOVEL_TIP}",
                    f"epoch {NOVEL_EPOCH}",
                    "kind grouped",
                    f"group {NOVEL_GROUP}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        with JOURNAL.open("a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "epoch": NOVEL_EPOCH,
                        "tip": NOVEL_TIP,
                        "state": "sealed",
                        "kind": "grouped",
                        "grid": "grid_n13.txt",
                        "bank": "bank_g7.txt",
                    }
                )
                + "\n"
            )
        RECEIPT.write_text(
            "pass = scoring\n"
            f"tip = {NOVEL_TIP}\n"
            f"epoch = {NOVEL_EPOCH}\n"
            f"group = {NOVEL_GROUP}\n"
            f"groups = {NOVEL_GROUPS}\n",
            encoding="utf-8",
        )
        rows, doc = _republish("novel")
        for sid in IDS:
            row = rows[sid]
            assert row["tip_epoch"] == NOVEL_EPOCH, (
                f"{sid}.tip_epoch did not move to the novel sealed generation"
            )
            assert row["group_size"] == NOVEL_GROUP, (
                f"{sid}.group_size did not move to the novel generation's width"
            )
            ppl = float(row["perplexity"])
            assert _finite(ppl) and ppl >= 1.0, f"{sid}.perplexity out of range"
            assert abs(ppl - float(base[sid]["perplexity"])) > COPY_GAP, (
                f"{sid}.perplexity did not move with the novel generation"
            )
        for cold, resume in PAIRS:
            assert abs(float(rows[cold]["perplexity"]) - float(rows[resume]["perplexity"])) <= (
                PAIR_TOL
            ), f"{cold}/{resume} stopped reproducing each other under the novel generation"
        assert doc.get("bands_ok") is False, (
            "bands_ok claims the novel generation lands inside the published bands"
        )
    finally:
        sheet.unlink(missing_ok=True)
        JOURNAL.write_bytes(journal)
        RECEIPT.write_bytes(receipt)
        _entry()
