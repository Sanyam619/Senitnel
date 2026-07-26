"""Verifier tests for AMR ghost-cell recovery outputs."""

import json
import re
from configparser import ConfigParser
from pathlib import Path

SUMMARY = Path("/output/restart-summary.json")
FORGE_HDR = Path("/app/include/forge.h")
POLICY_PATH = Path("/app/data/policy_v2.table")
SCENARIO_LABELS = ("alpha", "beta", "gamma")


def load_epsilons():
    text = FORGE_HDR.read_text()
    mass = float(re.search(r"#define\s+RESTART_DRIFT_CAP\s+([0-9.]+)f", text).group(1))
    face = float(re.search(r"#define\s+RESTART_FACE_CAP\s+([0-9.]+)f", text).group(1))
    schema = re.search(r'#define\s+RESTART_JSON_TAG\s+"([^"]+)"', text).group(1)
    return mass, face, schema


def load_policy():
    body = []
    for line in POLICY_PATH.read_text().splitlines():
        if line.startswith("active_") or line.startswith("reserve_"):
            continue
        body.append(line)
    parser = ConfigParser()
    parser.read_string("\n".join(body))
    policy = {}
    for label in SCENARIO_LABELS:
        sec = parser[label]
        policy[label] = {
            "block_tally": sec.getint("blocks"),
            "tree_depth": sec.getint("depth"),
            "face_count": sec.getint("face_count"),
        }
    return policy


MASS_EPS, FACE_L2_EPS, SCHEMA_TAG = load_epsilons()
POLICY = load_policy()

FIELD_DUMPS = [
    Path(f"/output/fields/{label}/{step}.bin")
    for label in SCENARIO_LABELS
    for step in ("t0", "t1")
]


def read_f32_le(data: bytes, offset: int = 0) -> float:
    bits = int.from_bytes(data[offset : offset + 4], "little")
    if bits == 0:
        return 0.0
    sign = -1.0 if bits & 0x80000000 else 1.0
    exp = (bits >> 23) & 0xFF
    mant = bits & 0x7FFFFF
    if exp == 0:
        return sign * mant / 8388608.0 * (2.0**-126)
    return sign * (1.0 + mant / 8388608.0) * (2.0 ** (exp - 127))


def read_field_pair(path: Path) -> tuple[float, float]:
    raw = path.read_bytes()[:8]
    return read_f32_le(raw, 0), read_f32_le(raw, 4)


def load_summary():
    assert SUMMARY.is_file(), "restart summary missing"
    return json.loads(SUMMARY.read_text())


class TestOutputs:
    def test_emit_json_contract(self):
        """Summary JSON exists with schema tag and required keys only."""
        data = load_summary()
        assert data["schema_tag"] == SCHEMA_TAG
        assert set(data.keys()) == {"schema_tag", "scenarios", "mass_drift", "tree_depth"}
        labels = {item["label"] for item in data["scenarios"]}
        assert labels == set(POLICY.keys())
        for item in data["scenarios"]:
            assert set(item.keys()) == {"label", "block_tally", "face_l2"}

    def test_field_dumps_present(self):
        """Each scenario emits t0 and t1 field dumps under /output/fields/."""
        for path in FIELD_DUMPS:
            assert path.is_file(), f"missing field dump {path}"
            assert path.stat().st_size >= 8, f"field dump too small {path}"

    def test_slice_l2_alpha(self):
        """Alpha scenario face-layer L2 stays within tolerance."""
        data = load_summary()
        alpha = next(s for s in data["scenarios"] if s["label"] == "alpha")
        assert alpha["face_l2"] < FACE_L2_EPS

    def test_slice_l2_beta(self):
        """Beta scenario face-layer L2 stays within tolerance."""
        data = load_summary()
        beta = next(s for s in data["scenarios"] if s["label"] == "beta")
        assert beta["face_l2"] < FACE_L2_EPS

    def test_mass_drift_within_epsilon(self):
        """Aggregate mass drift remains below the forge epsilon."""
        data = load_summary()
        assert data["mass_drift"] <= MASS_EPS

    def test_depth_alpha(self):
        """Alpha block tally and depth match the active layout directive."""
        data = load_summary()
        alpha = next(s for s in data["scenarios"] if s["label"] == "alpha")
        assert alpha["block_tally"] == POLICY["alpha"]["block_tally"]
        assert data["tree_depth"] >= POLICY["alpha"]["tree_depth"]

    def test_depth_beta(self):
        """Beta block tally matches the layout directive."""
        data = load_summary()
        beta = next(s for s in data["scenarios"] if s["label"] == "beta")
        assert beta["block_tally"] == POLICY["beta"]["block_tally"]

    def test_secondary_gamma(self):
        """Gamma chain requires full recovery pipeline and tolerances."""
        data = load_summary()
        gamma = next(s for s in data["scenarios"] if s["label"] == "gamma")
        assert gamma["face_l2"] < FACE_L2_EPS
        assert gamma["block_tally"] == POLICY["gamma"]["block_tally"]
        assert data["tree_depth"] >= POLICY["gamma"]["tree_depth"]

    def test_field_dump_matches_summary(self):
        """Per-scenario t0 dumps record the same face L2 reported in the summary."""
        data = load_summary()
        for item in data["scenarios"]:
            t0 = Path(f"/output/fields/{item['label']}/t0.bin")
            l2_stored, _mass = read_field_pair(t0)
            assert abs(l2_stored - item["face_l2"]) < 1e-5

    def test_summary_mass_matches_field_dumps(self):
        """Root mass_drift equals the mean per-scenario mass drift in t0 dumps."""
        data = load_summary()
        masses = []
        for label in SCENARIO_LABELS:
            _l2, mass = read_field_pair(Path(f"/output/fields/{label}/t0.bin"))
            masses.append(mass)
        mean_mass = sum(masses) / len(masses)
        assert abs(data["mass_drift"] - mean_mass) < 1e-5

    def test_per_scenario_mass_in_dumps(self):
        """Each t0 dump mass_drift field stays within the restart drift cap."""
        for label in SCENARIO_LABELS:
            _l2, mass = read_field_pair(Path(f"/output/fields/{label}/t0.bin"))
            assert mass <= MASS_EPS

    def test_layout_directive_consistency(self):
        """Every scenario block tally matches the policy table for its label."""
        data = load_summary()
        for item in data["scenarios"]:
            want = POLICY[item["label"]]["block_tally"]
            assert item["block_tally"] == want

    def test_t1_not_worse_than_t0(self):
        """Post-step face L2 in field dumps does not exceed the t0 measurement."""
        for label in SCENARIO_LABELS:
            t0_l2, _ = read_field_pair(Path(f"/output/fields/{label}/t0.bin"))
            t1_l2, _ = read_field_pair(Path(f"/output/fields/{label}/t1.bin"))
            assert t1_l2 <= t0_l2 + 1e-5
