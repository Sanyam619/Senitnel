"""Verifier for structured-prune-recovery-eval.

Grades /output/prune-eval.json against the published bands, the exact numbers a
faithful pass produces on the frozen snapshots, the geometry of the bound
channel roster, cold/resume parity, the entrypoint republish after a workspace
rebuild, and a novel durable roster inject.
"""

import json
import subprocess
from pathlib import Path

REPORT = Path("/output/prune-eval.json")
ENTRY = "/app/scripts/run_prune_eval.sh"
PIN = Path(__file__).resolve().parent / "data.sha256"
STAGE = Path("/logs/verifier")
JOURNAL = Path("/app/data/mask_registry/tip_journal.jsonl")
RECEIPT = Path("/app/serving/bind.accept")
TOPOLOGY = Path("/app/data/arch/topology.txt")
MASKS = Path("/app/data/masks")
SWEEP = Path("/app/data/fixtures/surface_ok.json")

IDS = ("cold_a", "resume_a", "cold_b", "resume_b", "mix_c", "mix_d")
PAIRS = (("cold_a", "resume_a"), ("cold_b", "resume_b"))

SCHEMA_TAG = "prune-eval-v2"
TIP_EXPECTED = 7
NUM_TOL = 1e-9
PAIR_TOL = 1e-4
COPY_GAP = 1e-4
GUARD = 0.04

SPARSITY_EXPECTED = 0.488571428571
FLOPS_EXPECTED = 0.535659833983

# Generations that must not be bound: 9 rolled back, 8 unstructured durable,
# 11 live overlay, 2 mid-run stamp, 3/4/5 remaining non-scoring rows.
ROLLED_BACK = 9
NOT_SCORING = (2, 3, 4, 5, 8, 11)

ACCURACY_EXPECTED = {
    "cold_a": 0.815,
    "resume_a": 0.815,
    "cold_b": 0.865,
    "resume_b": 0.865,
    "mix_c": 0.870,
    "mix_d": 0.890,
}

BANDS = {
    "cold_a": (0.795, 0.835),
    "resume_a": (0.795, 0.835),
    "cold_b": (0.845, 0.885),
    "resume_b": (0.845, 0.885),
    "mix_c": (0.850, 0.890),
    "mix_d": (0.870, 0.910),
}
SPARSITY_BAND = (0.478, 0.499)
FLOPS_BAND = (0.525, 0.546)

NOVEL_ROW = {"epoch": 13, "tip": "tip_n13", "state": "durable", "sheet": "m_n13.txt"}
NOVEL_KEEP = (
    (0, 1, 2, 3, 4, 5, 6, 11, 12, 13, 14, 15),
    (0, 1, 2, 4, 7, 8, 11, 12, 13, 15),
    (0, 1, 2, 3, 4, 6, 7, 9, 11),
)

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
    assert REPORT.is_file(), "entrypoint did not publish /output/prune-eval.json"
    return REPORT.read_bytes()


def _published():
    """The report as the agent left it, captured before any republish."""
    if "published" not in _CACHE:
        assert REPORT.is_file(), "missing /output/prune-eval.json"
        raw = REPORT.read_bytes()
        STAGE.mkdir(parents=True, exist_ok=True)
        (STAGE / "prune-eval-published.json").write_bytes(raw)
        _CACHE["published_raw"] = raw
        _CACHE["published"] = json.loads(raw.decode("utf-8"))
    return _CACHE["published"]


def _rebuilt():
    """The report the entrypoint publishes after rebuilding the workspace."""
    if "rebuilt" not in _CACHE:
        _published()
        raw = _entry()
        (STAGE / "prune-eval-rerun1.json").write_bytes(raw)
        _CACHE["rebuilt_raw"] = raw
        _CACHE["rebuilt"] = json.loads(raw.decode("utf-8"))
    return _CACHE["rebuilt"]


def _rows(doc):
    cells = doc.get("scenarios")
    assert isinstance(cells, list), "scenarios must be an array"
    got = [c.get("id") for c in cells]
    assert got == list(IDS), f"scenario ids/order mismatch: {got}"
    return {c["id"]: c for c in cells}


def _blocks():
    """(channels, inputs, cells) per block, plus the class count."""
    blocks = []
    classes = 0
    for line in TOPOLOGY.read_text(encoding="utf-8").splitlines():
        cells = line.split()
        if not cells:
            continue
        if cells[0] == "block":
            blocks.append((int(cells[2]), int(cells[3]), int(cells[4])))
        elif cells[0] == "classes":
            classes = int(cells[1])
    assert blocks and classes, "unreadable topology"
    return blocks, classes


def _geometry(counts):
    """Parameter and multiply shares of a channel roster, from the topology."""
    blocks, classes = _blocks()
    live_w = live_m = dense_w = dense_m = 0
    fan = blocks[0][1]
    for (channels, inputs, cost), rows in zip(blocks, counts):
        live_w += rows * fan
        live_m += rows * fan * cost
        dense_w += channels * inputs
        dense_m += channels * inputs * cost
        fan = rows
    live_w += classes * counts[-1]
    live_m += classes * counts[-1]
    dense_w += classes * blocks[-1][0]
    dense_m += classes * blocks[-1][0]
    return 1.0 - live_w / dense_w, live_m / dense_m


def _sweep_rows():
    doc = json.loads(SWEEP.read_text(encoding="utf-8"))
    return {r["id"]: r for r in doc["scenarios"]}


def _assert_accuracy_owns_the_row(rows):
    """A reported roster only describes the run when the accuracy beside it is
    in the neighbourhood the bands were measured in."""
    for sid in IDS:
        acc = float(rows[sid]["accuracy"])
        lo, hi = BANDS[sid]
        assert lo - GUARD <= acc <= hi + GUARD, (
            f"{sid}.accuracy {acc} could not have come from the reported roster"
        )


def test_frozen_inputs_integrity():
    """The architecture, the dense snapshots, the channel rosters, the
    registry, the calibration rows, the evaluation slices and the published
    bands must keep their shipped SHA-256 digests, and a report must have been
    published from them."""
    assert REPORT.is_file(), "missing /output/prune-eval.json"
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
    """Report carries the prune-eval-v2 tag, the six scenario ids in the
    published order, numeric accuracy and geometry in range, and an integer
    roster generation."""
    doc = _published()
    assert doc.get("schema_tag") == SCHEMA_TAG, "schema_tag mismatch"
    assert isinstance(doc.get("bands_ok"), bool), "bands_ok must be a boolean"
    rows = _rows(doc)
    for sid in IDS:
        row = rows[sid]
        for key in ("accuracy", "sparsity", "flops_frac"):
            v = row.get(key)
            assert isinstance(v, (int, float)) and not isinstance(v, bool), (
                f"{sid}.{key} must be a number"
            )
            assert _finite(v), f"{sid}.{key} must be finite"
            assert 0.0 <= float(v) <= 1.0, f"{sid}.{key} out of range"
        tip = row.get("mask_tip")
        assert isinstance(tip, int) and not isinstance(tip, bool), (
            f"{sid}.mask_tip must be an integer"
        )


def test_mask_tip_is_bound_durable_generation():
    """Every scenario reports the durable registry generation the desk binds,
    and the accuracy beside it comes from a pass under that roster."""
    rows = _rows(_rebuilt())
    for sid in IDS:
        got = rows[sid]["mask_tip"]
        assert got == TIP_EXPECTED, (
            f"{sid}.mask_tip {got} is not the bound durable generation"
        )
    _assert_accuracy_owns_the_row(rows)


def test_mask_tip_is_not_rolled_back_or_proposed_roster():
    """The rolled-back durable roster, the live overlay proposal and the stamp
    the mid-run snapshot carries must not be bound."""
    rows = _rows(_rebuilt())
    for sid in IDS:
        got = rows[sid]["mask_tip"]
        assert got != ROLLED_BACK, f"{sid}.mask_tip binds the rolled-back roster"
        assert got not in NOT_SCORING, f"{sid}.mask_tip binds a roster that is not scoring"
    _assert_accuracy_owns_the_row(rows)


def test_geometry_is_that_of_the_bound_roster():
    """Every scenario reports the geometry of the bound roster, propagated
    through the stack, and reports the same geometry as every other
    scenario."""
    rows = _rows(_rebuilt())
    for sid in IDS:
        sparsity = float(rows[sid]["sparsity"])
        flops = float(rows[sid]["flops_frac"])
        assert abs(sparsity - SPARSITY_EXPECTED) <= NUM_TOL, (
            f"{sid}.sparsity {sparsity} is not the bound roster's parameter share"
        )
        assert abs(flops - FLOPS_EXPECTED) <= NUM_TOL, (
            f"{sid}.flops_frac {flops} is not the bound roster's multiply share"
        )
    _assert_accuracy_owns_the_row(rows)


def test_cold_and_resume_partners_agree():
    """A cold scenario and its resume partner are one measurement taken from
    two starting points, so their accuracies agree to within 1e-4."""
    rows = _rows(_rebuilt())
    for cold, resume in PAIRS:
        left = float(rows[cold]["accuracy"])
        right = float(rows[resume]["accuracy"])
        assert abs(left - right) <= PAIR_TOL, (
            f"{cold}/{resume} accuracies {left}/{right} do not reproduce each other"
        )
    _assert_accuracy_owns_the_row(rows)


def _assert_accuracy(sids):
    rows = _rows(_rebuilt())
    for sid in sids:
        acc = float(rows[sid]["accuracy"])
        want = ACCURACY_EXPECTED[sid]
        assert abs(acc - want) <= NUM_TOL, (
            f"{sid}.accuracy {acc} does not match a faithful pass ({want})"
        )


def test_first_domain_scenarios_match_faithful_pass():
    """The scenarios scored on the first input domain carry the accuracy a
    faithful pass produces on the frozen snapshots."""
    _assert_accuracy(("cold_a", "resume_a"))


def test_second_domain_scenarios_match_faithful_pass():
    """The scenarios scored on the second input domain carry the accuracy a
    faithful pass produces on the frozen snapshots."""
    _assert_accuracy(("cold_b", "resume_b"))


def test_mixed_domain_scenarios_match_faithful_pass():
    """The mixed-domain scenarios carry the accuracy a faithful pass produces
    on the frozen snapshots."""
    _assert_accuracy(("mix_c", "mix_d"))


def test_all_scenarios_inside_published_bands():
    """Every published scenario lands inside its accuracy band and both
    geometry bands, and bands_ok is true."""
    doc = _rebuilt()
    rows = _rows(doc)
    for sid in IDS:
        acc = float(rows[sid]["accuracy"])
        lo, hi = BANDS[sid]
        assert lo <= acc <= hi, f"{sid}.accuracy {acc} outside published band"
        sparsity = float(rows[sid]["sparsity"])
        flops = float(rows[sid]["flops_frac"])
        assert SPARSITY_BAND[0] <= sparsity <= SPARSITY_BAND[1], (
            f"{sid}.sparsity {sparsity} outside published band"
        )
        assert FLOPS_BAND[0] <= flops <= FLOPS_BAND[1], (
            f"{sid}.flops_frac {flops} outside published band"
        )
    assert doc.get("bands_ok") is True, "bands_ok is not true"


def test_published_numbers_are_not_the_captured_sweep():
    """Numbers must come from scoring the frozen snapshots, not from the
    captured sweep fixture."""
    rows = _rows(_rebuilt())
    sweep = _sweep_rows()
    for sid in IDS:
        if sid not in sweep:
            continue
        moved = abs(float(rows[sid]["accuracy"]) - float(sweep[sid]["accuracy"]))
        assert moved > COPY_GAP, f"{sid} accuracy was copied from the captured sweep"


def test_entrypoint_republish_is_byte_identical():
    """The report the agent published must equal what the entrypoint publishes
    after rebuilding the workspace, and a second republish must match too."""
    first = _rebuilt()
    assert first is not None
    assert _CACHE["published_raw"] == _CACHE["rebuilt_raw"], (
        "published report differs from the report the rebuilt workspace emits"
    )
    again = _entry()
    (STAGE / "prune-eval-rerun2.json").write_bytes(again)
    assert again == _CACHE["rebuilt_raw"], "two consecutive republishes differ"


def test_novel_durable_roster_moves_the_report():
    """A durable channel roster the desk has never seen must move the bound
    generation, the geometry and every accuracy together."""
    base = _rows(_rebuilt())
    journal = JOURNAL.read_bytes()
    receipt = RECEIPT.read_bytes()
    sheet = MASKS / NOVEL_ROW["sheet"]
    body = [f"tip {NOVEL_ROW['tip']}", f"epoch {NOVEL_ROW['epoch']}", "kind structured"]
    for at, keep in enumerate(NOVEL_KEEP):
        body.append(f"keep {at} " + " ".join(str(i) for i in keep))
    want_sparsity, want_flops = _geometry([len(k) for k in NOVEL_KEEP])
    try:
        sheet.write_text("\n".join(body) + "\n", encoding="utf-8")
        with JOURNAL.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(NOVEL_ROW) + "\n")
            RECEIPT.write_text(
                "desk_pass = scoring\n"
                f"bound_tip = {NOVEL_ROW['tip']}\n"
                f"bound_epoch = {NOVEL_ROW['epoch']}\n"
                f"kept_channels = {sum(len(k) for k in NOVEL_KEEP)}\n",
                encoding="utf-8",
            )
        raw = _entry()
        (STAGE / "prune-eval-novel.json").write_bytes(raw)
        doc = json.loads(raw.decode("utf-8"))
        rows = _rows(doc)
        for sid in IDS:
            row = rows[sid]
            assert row["mask_tip"] == NOVEL_ROW["epoch"], (
                f"{sid}.mask_tip did not move to the novel durable generation"
            )
            sparsity = float(row["sparsity"])
            flops = float(row["flops_frac"])
            assert abs(sparsity - want_sparsity) <= NUM_TOL, (
                f"{sid}.sparsity {sparsity} is not the novel roster's parameter share"
            )
            assert abs(flops - want_flops) <= NUM_TOL, (
                f"{sid}.flops_frac {flops} is not the novel roster's multiply share"
            )
            acc = float(row["accuracy"])
            assert 0.0 <= acc <= 1.0, f"{sid}.accuracy {acc} out of range"
            assert abs(acc - float(base[sid]["accuracy"])) > COPY_GAP, (
                f"{sid}.accuracy did not move with the novel roster"
            )
        for cold, resume in PAIRS:
            left = float(rows[cold]["accuracy"])
            right = float(rows[resume]["accuracy"])
            assert abs(left - right) <= PAIR_TOL, (
                f"{cold}/{resume} stopped reproducing each other under the novel roster"
            )
        assert doc.get("bands_ok") is False, (
            "bands_ok claims the novel roster lands inside the published bands"
        )
    finally:
        sheet.unlink(missing_ok=True)
        JOURNAL.write_bytes(journal)
        RECEIPT.write_bytes(receipt)
        _entry()
