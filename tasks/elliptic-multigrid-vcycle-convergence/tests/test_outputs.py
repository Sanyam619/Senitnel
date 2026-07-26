"""Verifier tests for elliptic-multigrid-vcycle-convergence.

These tests inspect the artifacts produced under ``/app/output`` by
the freshly rebuilt ``/app/elliptic_mg`` binary. The session-scoped
``regenerate_solver_outputs`` fixture in ``conftest.py`` wipes the
output directory, rebuilds via ``make`` from ``/app``, and invokes the
binary directly before any test reads a file, so pre-existing outputs
cannot mask a broken solver.
"""

from __future__ import annotations

import json
import math
import re
import struct
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Configuration mirrored from environment/data and environment/include.
# ---------------------------------------------------------------------------

SCENARIOS = ["s_iso", "s_aniso", "s_jump", "s_corner", "s_mixed"]
OUTPUT_JSON = Path("/app/output/convergence.json")
TRACE_DIR = Path("/app/output/traces")
FIELD_DIR = Path("/app/output/fields")
BUDGETS_TABLE = Path("/app/data/policy/budgets.table")
SOLVER_CONFIG_H = Path("/app/include/solver_config.h")
DESC_DIR = Path("/app/data/scenarios")

# Canonical (verifier-owned) budgets and residual target. The env-side
# files must match these; tests reject any weakening of these numbers.
CANONICAL_BUDGETS: dict[str, int] = {
    "s_iso": 7,
    "s_aniso": 7,
    "s_jump": 11,
    "s_corner": 10,
    "s_mixed": 8,
}
CANONICAL_RESIDUAL_TARGET = 1.0e-8
CANONICAL_SOLVER_TAG = "elliptic-mg-v1"

# Expected geometry: 65 x 65 nodes with float64 storage.
NX = 65
NY = 65
FIELD_BYTES = NX * NY * 8


# ---------------------------------------------------------------------------
# Small helpers.
# ---------------------------------------------------------------------------

def _parse_header_double(path: Path, name: str) -> float:
    text = path.read_text()
    m = re.search(rf"#define\s+{name}\s+([\-0-9eE.+]+)", text)
    if not m:
        raise AssertionError(f"{name} not found in {path}")
    return float(m.group(1))


def _parse_header_string(path: Path, name: str) -> str:
    text = path.read_text()
    m = re.search(rf'#define\s+{name}\s+"([^"]+)"', text)
    if not m:
        raise AssertionError(f"{name} string not found in {path}")
    return m.group(1)


def _parse_header_int(path: Path, name: str) -> int:
    text = path.read_text()
    m = re.search(rf"#define\s+{name}\s+(\d+)", text)
    if not m:
        raise AssertionError(f"{name} int not found in {path}")
    return int(m.group(1))


def _load_budget_table() -> dict[str, int]:
    result: dict[str, int] = {}
    for line in BUDGETS_TABLE.read_text().splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        if len(parts) < 2:
            continue
        try:
            result[parts[0]] = int(parts[1])
        except ValueError:
            continue
    return result


@pytest.fixture(scope="module")
def report() -> dict:
    assert OUTPUT_JSON.exists(), (
        f"{OUTPUT_JSON} not found; did /app/scripts/run_solve.sh run?"
    )
    return json.loads(OUTPUT_JSON.read_text())


@pytest.fixture(scope="module")
def scenario_map(report: dict) -> dict[str, dict]:
    scenarios = report.get("scenarios")
    assert isinstance(scenarios, list) and scenarios, "scenarios list missing/empty"
    return {s["label"]: s for s in scenarios}


@pytest.fixture(scope="module")
def budgets() -> dict[str, int]:
    return dict(CANONICAL_BUDGETS)


@pytest.fixture(scope="module")
def residual_target() -> float:
    return CANONICAL_RESIDUAL_TARGET


@pytest.fixture(scope="module")
def solver_tag() -> str:
    return CANONICAL_SOLVER_TAG


@pytest.fixture(scope="module")
def max_outer() -> int:
    return _parse_header_int(SOLVER_CONFIG_H, "MAX_OUTER_ITERATIONS")


# ---------------------------------------------------------------------------
# JSON structure + solver identity.
# ---------------------------------------------------------------------------

def test_output_json_is_valid_object(report):
    """convergence.json is a JSON object with the required top-level keys."""
    assert isinstance(report, dict)
    for key in ("solver_tag", "scenarios", "all_within_budget"):
        assert key in report, f"missing top-level key: {key}"


def test_solver_tag_matches_header(report, solver_tag):
    """solver_tag in the report matches SOLVER_TAG in solver_config.h."""
    assert report["solver_tag"] == solver_tag


def test_all_expected_scenarios_present(scenario_map):
    """All five configured scenarios show up in the report."""
    assert sorted(scenario_map.keys()) == sorted(SCENARIOS)


def test_scenario_entries_have_required_keys(scenario_map):
    """Each scenario entry declares label, iterations, residual, budget."""
    for label, entry in scenario_map.items():
        for key in ("label", "iterations", "residual", "budget"):
            assert key in entry, f"{label}: missing key {key}"


def test_scenario_budgets_match_reference_table(scenario_map, budgets):
    """Reported per-scenario budget matches budgets.table (no weakening)."""
    for label in SCENARIOS:
        assert scenario_map[label]["budget"] == budgets[label], (
            f"{label}: reported budget {scenario_map[label]['budget']} "
            f"does not match reference {budgets[label]}"
        )


# ---------------------------------------------------------------------------
# Per-scenario convergence checks (the hard tests).
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("label", SCENARIOS)
def test_scenario_converges_within_budget(label, scenario_map, budgets):
    """Scenario reached the residual target in at most `budget` V-cycles."""
    entry = scenario_map[label]
    budget = budgets[label]
    assert 1 <= entry["iterations"] <= budget, (
        f"{label}: iterations={entry['iterations']} not in [1, {budget}]"
    )


@pytest.mark.parametrize("label", SCENARIOS)
def test_scenario_residual_meets_target(label, scenario_map, residual_target):
    """Scenario's reported residual is finite and at or below the target."""
    entry = scenario_map[label]
    assert math.isfinite(entry["residual"]), (
        f"{label}: residual={entry['residual']} must be finite"
    )
    assert entry["residual"] >= 0.0, (
        f"{label}: residual={entry['residual']} must be non-negative"
    )
    assert entry["residual"] <= residual_target, (
        f"{label}: residual={entry['residual']:.3e} exceeds "
        f"target {residual_target:.3e}"
    )


def test_all_within_budget_flag_consistent(report, scenario_map, budgets,
                                            residual_target):
    """`all_within_budget` truthfully summarises per-scenario success."""
    expected = all(
        scenario_map[label]["iterations"] <= budgets[label]
        and scenario_map[label]["residual"] <= residual_target
        for label in SCENARIOS
    )
    assert report["all_within_budget"] is expected


def test_no_scenario_uses_max_outer_cap(scenario_map, max_outer):
    """No scenario is right at the MAX_OUTER_ITERATIONS ceiling (stall)."""
    for label, entry in scenario_map.items():
        assert entry["iterations"] < max_outer, (
            f"{label}: solver hit MAX_OUTER_ITERATIONS={max_outer}"
        )


# ---------------------------------------------------------------------------
# Trace-file checks (residual history, monotone descent).
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("label", SCENARIOS)
def test_trace_length_matches_reported_iterations(label, scenario_map):
    """Trace line count equals the iterations field reported in JSON."""
    path = TRACE_DIR / f"{label}.trace"
    assert path.exists(), f"missing trace file: {path}"
    lines = [ln for ln in path.read_text().splitlines() if ln.strip()]
    assert len(lines) == scenario_map[label]["iterations"], (
        f"{label}: trace has {len(lines)} lines, "
        f"iterations={scenario_map[label]['iterations']}"
    )


@pytest.mark.parametrize("label", SCENARIOS)
def test_trace_is_positive_and_finite(label):
    """Every trace entry is a finite non-negative residual value."""
    path = TRACE_DIR / f"{label}.trace"
    values = [float(x) for x in path.read_text().split()]
    for v in values:
        assert math.isfinite(v), f"{label}: non-finite residual in trace"
        assert v >= 0.0, f"{label}: negative residual {v} in trace"


@pytest.mark.parametrize("label", SCENARIOS)
def test_trace_final_value_matches_reported_residual(label, scenario_map):
    """Trace tail agrees with the residual field reported in JSON."""
    path = TRACE_DIR / f"{label}.trace"
    values = [float(x) for x in path.read_text().split()]
    reported = scenario_map[label]["residual"]
    if not values:
        pytest.fail(f"{label}: trace empty")
    tail = values[-1]
    # The reported residual should equal (or be very close to) the last
    # trace entry. Allow relative tolerance for text round-tripping.
    assert math.isclose(tail, reported, rel_tol=1e-9, abs_tol=1e-18), (
        f"{label}: trace tail {tail:.6e} vs reported {reported:.6e}"
    )


@pytest.mark.parametrize("label", SCENARIOS)
def test_trace_is_monotone_non_increasing(label):
    """Residual history is non-increasing (multigrid should not diverge)."""
    path = TRACE_DIR / f"{label}.trace"
    values = [float(x) for x in path.read_text().split()]
    for i in range(1, len(values)):
        # Allow a tiny numerical wiggle; multigrid should not diverge.
        assert values[i] <= values[i - 1] * (1.0 + 1e-6), (
            f"{label}: residual increased at step {i}: "
            f"{values[i - 1]:.6e} -> {values[i]:.6e}"
        )


@pytest.mark.parametrize("label", SCENARIOS)
def test_trace_exhibits_multigrid_convergence_rate(label, scenario_map,
                                                     residual_target):
    """Multi-cycle runs must show average geometric reduction <= 0.4.
    A single V-cycle that already meets the residual target satisfies the
    instruction's rate requirement (one-cycle reduction is stronger than
    the multi-cycle bound).
    """
    path = TRACE_DIR / f"{label}.trace"
    values = [float(x) for x in path.read_text().split()]
    assert values, f"{label}: trace empty"
    if len(values) == 1:
        assert scenario_map[label]["residual"] <= residual_target, (
            f"{label}: single-cycle residual "
            f"{scenario_map[label]['residual']:.3e} exceeds target "
            f"{residual_target:.3e}"
        )
        return
    if values[0] == 0.0:
        assert values[-1] == 0.0
        return
    ratio = (values[-1] / values[0]) ** (1.0 / (len(values) - 1))
    assert ratio <= 0.4, (
        f"{label}: average per-V-cycle reduction factor {ratio:.3f} "
        "exceeds 0.4 — solver is not multigrid-quality"
    )


# ---------------------------------------------------------------------------
# Field-file checks.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("label", SCENARIOS)
def test_field_file_exists_with_expected_size(label):
    """Field dump is present with the exact expected byte count."""
    path = FIELD_DIR / f"{label}.f64"
    assert path.exists(), f"missing field file: {path}"
    assert path.stat().st_size == FIELD_BYTES, (
        f"{label}: field size {path.stat().st_size} != expected {FIELD_BYTES}"
    )


@pytest.mark.parametrize("label", SCENARIOS)
def test_field_is_finite_and_nontrivial(label):
    """Field values are finite and the solution is not the zero field."""
    path = FIELD_DIR / f"{label}.f64"
    data = path.read_bytes()
    n = NX * NY
    vals = struct.unpack(f"<{n}d", data)
    for v in vals:
        assert math.isfinite(v), f"{label}: non-finite value in field"
    # A well-solved elliptic PDE with a positive source should have a
    # nonzero interior maximum.
    max_abs = max(abs(v) for v in vals)
    assert max_abs > 1e-6, (
        f"{label}: field peak {max_abs:.3e} looks like an untouched zero field"
    )


@pytest.mark.parametrize("label", SCENARIOS)
def test_field_boundary_is_dirichlet_zero(label):
    """Boundary rows/columns are exactly zero (Dirichlet BC preserved)."""
    path = FIELD_DIR / f"{label}.f64"
    data = path.read_bytes()
    n = NX * NY
    vals = struct.unpack(f"<{n}d", data)
    # Grid layout: index(i, j) = i * NY + j.
    for i in range(NX):
        for j in (0, NY - 1):
            assert vals[i * NY + j] == 0.0, (
                f"{label}: boundary node ({i},{j}) not zero"
            )
    for j in range(NY):
        for i in (0, NX - 1):
            assert vals[i * NY + j] == 0.0, (
                f"{label}: boundary node ({i},{j}) not zero"
            )


# ---------------------------------------------------------------------------
# Anti-cheat: scenario descriptors and policy files must not have been
# mutated to weaken the acceptance criteria.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("label", SCENARIOS)
def test_scenario_descriptor_present_and_matches_budget(label, budgets):
    """Descriptor files still exist and their `budget=` values were not lowered."""
    desc = DESC_DIR / f"{label}.desc"
    assert desc.exists(), f"missing scenario descriptor: {desc}"
    text = desc.read_text()
    m = re.search(r"^\s*budget\s*=\s*(\d+)", text, re.MULTILINE)
    assert m, f"{label}: no 'budget = N' line in descriptor"
    assert int(m.group(1)) == budgets[label], (
        f"{label}: descriptor budget {m.group(1)} differs from canonical "
        f"budget {budgets[label]} (do not weaken budgets)"
    )


def test_policy_budgets_table_matches_canonical():
    """The on-disk policy table matches the verifier's canonical budgets."""
    on_disk = _load_budget_table()
    for label, canonical in CANONICAL_BUDGETS.items():
        assert on_disk.get(label) == canonical, (
            f"{label}: policy table has {on_disk.get(label)}, "
            f"canonical is {canonical}"
        )


def test_residual_target_not_relaxed():
    """The compiled residual target has not been increased."""
    on_disk = _parse_header_double(SOLVER_CONFIG_H, "RESIDUAL_TARGET")
    assert on_disk <= CANONICAL_RESIDUAL_TARGET, (
        f"residual target on disk {on_disk} is looser than canonical "
        f"{CANONICAL_RESIDUAL_TARGET}"
    )


def test_solver_tag_header_matches_canonical():
    """Solver tag literal in the header is unchanged."""
    on_disk = _parse_header_string(SOLVER_CONFIG_H, "SOLVER_TAG")
    assert on_disk == CANONICAL_SOLVER_TAG, (
        f"SOLVER_TAG on disk {on_disk!r} differs from canonical "
        f"{CANONICAL_SOLVER_TAG!r}"
    )
