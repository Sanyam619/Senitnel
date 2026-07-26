"""Hard invariant checks for the LoRA adapter merge report.

Also drives the verifier-owned probe program that imports the current
pipeline packages directly (staged and built by conftest.py), so a
hand-authored /output/merge-report.json or a doctored driver cannot mask
defects that the underlying components must fix.
"""

from __future__ import annotations

import json
from pathlib import Path

REPORT = Path("/output/merge-report.json")

ADAPTER_LABELS = ("alpha", "beta", "gamma", "delta")
TASK_IDS = ("task_1", "task_2", "task_3", "task_4", "task_5")
NO_REGRESSION_TOL = 1.0e-8
RESIDUAL_TOL = 1.0e-9


def load_report() -> dict:
    assert REPORT.is_file(), f"merge report missing at {REPORT}"
    return json.loads(REPORT.read_text())


def is_finite(x) -> bool:
    if not isinstance(x, (int, float)):
        return False
    # NaN != itself; +/-inf compares as inf.
    return x == x and x not in (float("inf"), float("-inf"))


class TestReportSurface:
    def test_report_schema_tag(self):
        """Report file exists and carries the expected schema tag."""
        data = load_report()
        assert data.get("schema_tag") == "lora-merge-v1"

    def test_top_level_sections(self):
        """Report has exactly the three documented sections plus schema tag."""
        data = load_report()
        assert set(data.keys()) == {"schema_tag", "adapters", "evaluation", "attribution"}

    def test_adapters_section_shape(self):
        """Adapters section has one entry per label with the documented fields."""
        data = load_report()
        adapters = data["adapters"]
        assert len(adapters) == len(ADAPTER_LABELS)
        seen = {row["label"] for row in adapters}
        assert seen == set(ADAPTER_LABELS)
        for row in adapters:
            assert set(row.keys()) == {
                "label", "source_snapshot", "target_snapshot",
                "rebased_norm", "contribution_norm",
            }
            assert row["target_snapshot"] == "S3"
            assert row["source_snapshot"] in ("S1", "S2", "S3")
            assert is_finite(row["rebased_norm"])
            assert is_finite(row["contribution_norm"])
            assert row["rebased_norm"] >= 0.0
            assert row["contribution_norm"] >= 0.0

    def test_evaluation_section_shape(self):
        """Evaluation section has one entry per task with per-adapter decommission scores."""
        data = load_report()
        rows = data["evaluation"]
        assert len(rows) == len(TASK_IDS)
        seen = {row["task_id"] for row in rows}
        assert seen == set(TASK_IDS)
        for row in rows:
            assert set(row.keys()) == {"task_id", "baseline_score", "merged_score", "decommission_scores"}
            assert is_finite(row["baseline_score"])
            assert is_finite(row["merged_score"])
            dec = row["decommission_scores"]
            assert set(dec.keys()) == set(ADAPTER_LABELS)
            for label in ADAPTER_LABELS:
                assert is_finite(dec[label])

    def test_attribution_section_shape(self):
        """Attribution section has the three documented aggregate fields."""
        data = load_report()
        attr = data["attribution"]
        assert set(attr.keys()) == {
            "total_delta_frobenius",
            "sum_per_adapter_frobenius_squared",
            "residual_after_all_decommission",
        }
        for k, v in attr.items():
            assert is_finite(v), f"{k} not finite: {v!r}"
            assert v >= 0.0


class TestNumericInvariants:
    def test_contribution_norms_nonzero(self):
        """Every adapter contributes a non-trivial amount to the merged state."""
        data = load_report()
        for row in data["adapters"]:
            assert row["contribution_norm"] > 1e-6, (
                f"{row['label']} contribution_norm={row['contribution_norm']} "
                "suggests per-source shares were not populated"
            )
            assert row["rebased_norm"] > 1e-6, row

    def test_contribution_matches_rebased(self):
        """Each adapter's contribution equals its full effective delta post-rebase."""
        data = load_report()
        for row in data["adapters"]:
            assert abs(row["contribution_norm"] - row["rebased_norm"]) <= 1.0e-9, row

    def test_no_downstream_regression(self):
        """Every merged_score is at least baseline_score minus the evaluator tolerance."""
        data = load_report()
        for row in data["evaluation"]:
            assert row["merged_score"] >= row["baseline_score"] - NO_REGRESSION_TOL, (
                f"{row['task_id']} regressed: baseline={row['baseline_score']} "
                f"merged={row['merged_score']}"
            )

    def test_decommission_recovers_baseline_absence(self, run_verify_fixture):
        """Removing gamma from the merged state recovers the score of a fresh
        merge that omitted gamma. The verifier recomputes the reference score
        by driving the pipeline packages directly with the current sources.
        """
        run_verify_fixture("gamma_recovers")

    def test_attribution_residual_small(self):
        """The full merged delta equals the sum of per-adapter contributions."""
        data = load_report()
        r = data["attribution"]["residual_after_all_decommission"]
        assert r <= RESIDUAL_TOL, (
            f"residual attribution exceeds tolerance: got {r} vs {RESIDUAL_TOL}; "
            "per-source shares do not account for the full merged delta"
        )


class TestPipelineComponents:
    """Behavioral probes against the current pipeline packages.

    conftest.py stages a small verifier-owned probe under the source tree,
    rebuilds all classes, and exposes ``run_verify`` to invoke individual
    subcommands. Each subcommand exercises one component with inputs the
    verifier picks, so a hand-authored merge-report.json cannot satisfy
    them without the components themselves being correct.
    """

    def test_align_identity(self, run_verify_fixture):
        """Rebasing from-and-to the same snapshot must be a no-op on the deltas."""
        run_verify_fixture("align_identity")

    def test_align_scale_preserves_marginal(self, run_verify_fixture):
        """Rebasing across a normalizer retune must preserve the adapter's
        residual-block marginal on shared tokens."""
        run_verify_fixture("align_scale")

    def test_align_vocab(self, run_verify_fixture):
        """Rebasing across a vocab-size change must resize the embedding delta."""
        run_verify_fixture("align_vocab")

    def test_fuse_per_source_shares(self, run_verify_fixture):
        """Fusion must expose per-source shares that equal the input aligned deltas."""
        run_verify_fixture("fuse_shares")

    def test_exclude_roundtrip(self, run_verify_fixture):
        """Excluding a source then re-adding its share reconstructs the merged delta."""
        run_verify_fixture("roundtrip")

    def test_exclude_equals_reblend(self, run_verify_fixture):
        """Excluding a source equals blending the remaining sources from scratch."""
        run_verify_fixture("reblend_eq")
