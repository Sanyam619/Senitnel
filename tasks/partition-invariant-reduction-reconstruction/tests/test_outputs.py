import json
import subprocess
from pathlib import Path

import pytest

LAYOUTS = ["pack_1", "pack_2", "pack_4", "pack_8"]
SCENARIOS = ["tape_alpha", "tape_beta", "tape_gamma"]
REDUCTIONS = Path("/output/reductions.json")
OWNERSHIP = Path("/output/ownership.json")
WS_ROOT = Path("/app/ws")
CK_DIR = Path("/app/data/checkpoints")


@pytest.fixture(scope="module", autouse=True)
def rebuild_and_run():
    """Rebuild the runner from sources and emit output artifacts."""
    subprocess.run(
        ["cargo", "build", "--release", "--locked", "--offline"],
        cwd=WS_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            "cargo",
            "run",
            "--release",
            "--locked",
            "--offline",
            "-p",
            "m5",
            "--",
            "all-layouts",
            "--out-dir",
            "/output",
        ],
        cwd=WS_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _f64_bits(x: float) -> str:
    # Big-endian IEEE754 hex for finite non-zero fixtures (no opaque hex literals).
    neg = (x < 0.0) or (x == 0.0 and str(x).startswith("-"))
    ax = -x if x < 0.0 else x
    assert ax > 0.0 and ax != float("inf") and ax == ax
    exp = 0
    while ax >= 2.0:
        ax *= 0.5
        exp += 1
    while ax < 1.0:
        ax *= 2.0
        exp -= 1
    frac = ax - 1.0
    mant = 0
    for _ in range(52):
        frac *= 2.0
        bit = 1 if frac >= 1.0 else 0
        mant = (mant << 1) | bit
        if bit:
            frac -= 1.0
    biased = exp + 1023
    assert 0 < biased < 2047
    sign = 1 if neg else 0
    bits = (sign << 63) | (biased << 52) | mant
    return f"{bits:016x}"


def _kahan_sum(values) -> float:
    # For dyadic fixtures, plain left-to-right summation is bit-stable and
    # matches a careful Rust accumulator without depending on FMA quirks.
    total = 0.0
    for v in values:
        total = total + v
    return total


def _canonical_for_scenario(scenario: str) -> dict[str, str]:
    ck = json.loads((CK_DIR / f"{scenario}.json").read_text())
    a, b, wts = ck["a"], ck["b"], ck["w"]
    n = ck["length"]
    ordered = range(n)
    return {
        "sum_w_bits": _f64_bits(_kahan_sum(wts[i] * a[i] for i in ordered)),
        "dot_ab_bits": _f64_bits(_kahan_sum(a[i] * b[i] for i in ordered)),
        "l2_sq_bits": _f64_bits(_kahan_sum(a[i] * a[i] for i in ordered)),
    }


def _load_rows() -> list[dict]:
    assert REDUCTIONS.exists(), "missing reductions.json"
    return json.loads(REDUCTIONS.read_text())


def _index_rows(rows: list[dict]) -> dict[tuple[str, str], dict]:
    out: dict[tuple[str, str], dict] = {}
    for row in rows:
        key = (row["layout"], row["scenario"])
        out[key] = row
    return out


def _expected_overlap_owners(layout: str) -> dict[str, int]:
    ranks = int(layout.split("_")[1])
    chunk = 512 // ranks
    owners: dict[str, int] = {}
    for r in range(ranks - 1):
        owners[str((r + 1) * chunk)] = r
    return owners


def test_reductions_file_exists():
    """reductions.json must be written under /output."""
    assert REDUCTIONS.exists()


def test_ownership_file_exists():
    """ownership.json must be written under /output."""
    assert OWNERSHIP.exists()


def test_reductions_row_schema():
    """Each reductions row must expose layout, scenario, and the three bit columns."""
    for row in _load_rows():
        assert isinstance(row.get("layout"), str)
        assert isinstance(row.get("scenario"), str)
        assert isinstance(row.get("sum_w_bits"), str)
        assert isinstance(row.get("dot_ab_bits"), str)
        assert isinstance(row.get("l2_sq_bits"), str)


def test_all_layout_scenario_pairs_present():
    """Every layout and tape_* checkpoint pair must appear in reductions.json."""
    rows = _index_rows(_load_rows())
    for layout in LAYOUTS:
        for scenario in SCENARIOS:
            assert (layout, scenario) in rows, f"missing {layout}/{scenario}"


def test_only_tape_scenarios_emitted():
    """reductions.json should only include tape_* checkpoint scenarios."""
    for row in _load_rows():
        assert row["scenario"].startswith("tape_"), row["scenario"]


def test_scalars_match_canonical_bits():
    """Scalar bit patterns must match a full-domain index-order reduction of each tape."""
    rows = _index_rows(_load_rows())
    for scenario in SCENARIOS:
        exp = _canonical_for_scenario(scenario)
        for layout in LAYOUTS:
            row = rows[(layout, scenario)]
            assert row["sum_w_bits"] == exp["sum_w_bits"], f"sum_w {layout} {scenario}"
            assert row["dot_ab_bits"] == exp["dot_ab_bits"], f"dot_ab {layout} {scenario}"
            assert row["l2_sq_bits"] == exp["l2_sq_bits"], f"l2_sq {layout} {scenario}"


def test_pack1_matches_canonical():
    """Even the single-rank packing must match the canonical bit patterns."""
    rows = _index_rows(_load_rows())
    for scenario in SCENARIOS:
        exp = _canonical_for_scenario(scenario)
        row = rows[("pack_1", scenario)]
        assert row["sum_w_bits"] == exp["sum_w_bits"]
        assert row["dot_ab_bits"] == exp["dot_ab_bits"]
        assert row["l2_sq_bits"] == exp["l2_sq_bits"]


def test_cross_layout_bit_agreement():
    """All rank packings must agree with each other on every tape scenario."""
    rows = _index_rows(_load_rows())
    for scenario in SCENARIOS:
        ref = rows[("pack_1", scenario)]
        for layout in LAYOUTS[1:]:
            row = rows[(layout, scenario)]
            assert row["sum_w_bits"] == ref["sum_w_bits"]
            assert row["dot_ab_bits"] == ref["dot_ab_bits"]
            assert row["l2_sq_bits"] == ref["l2_sq_bits"]


def test_weighted_sum_uses_stored_weights():
    """sum_w_bits must reflect the on-disk weight lane, not a shifted copy."""
    rows = _index_rows(_load_rows())
    for scenario in SCENARIOS:
        exp = _canonical_for_scenario(scenario)
        for layout in LAYOUTS:
            assert rows[(layout, scenario)]["sum_w_bits"] == exp["sum_w_bits"]


def test_overlap_ownership_map():
    """ownership.json must assign each interior boundary to the lower-numbered rank."""
    owners = json.loads(OWNERSHIP.read_text())
    for layout in LAYOUTS:
        assert layout in owners, f"missing layout {layout} in ownership.json"
        got = owners[layout]
        exp = _expected_overlap_owners(layout)
        assert got == exp, f"ownership mismatch for {layout}"


def test_overlap_stress_not_double_counted():
    """tape_gamma under multi-rank packings must still match the canonical sum_w bits."""
    rows = _index_rows(_load_rows())
    exp = _canonical_for_scenario("tape_gamma")
    for layout in ("pack_2", "pack_4", "pack_8"):
        row = rows[(layout, "tape_gamma")]
        assert row["sum_w_bits"] == exp["sum_w_bits"]
