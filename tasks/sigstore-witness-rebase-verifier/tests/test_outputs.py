"""Verifier for witness rebase transparency-log decisions."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

VERDICTS = Path("/output/verdicts.json")
DATA = Path("/data")
EVENTS_DIR = DATA / "events"
SHARDS_DIR = DATA / "shards"
SCRIPTS = Path("/app/scripts")
BIN = Path("/app/bin/vfy")

ACCEPT_REASONS = {
    "pre_rotation_ok",
    "transitional_ok",
    "post_rotation_ok",
    "dual_attest_ok",
    "signer_valid_at_time",
}
REJECT_REASONS = {
    "threshold_shortfall",
    "cross_shard_unattested",
    "checkpoint_unbound",
}

# Ground-truth partition (embedded in test code, not read from env).
EARLY = {f"e{i:02d}" for i in range(1, 7)}
MID = {f"e{i:02d}" for i in range(7, 13)}
LATE = {f"e{i:02d}" for i in range(13, 19)}
DUAL = {f"e{i:02d}" for i in range(19, 25)}
REVOKED = {f"e{i:02d}" for i in range(25, 31)}
UNDERWEIGHT = {f"e{i:02d}" for i in range(31, 35)}
SHARD_BOUNDARY = {f"e{i:02d}" for i in range(35, 41)}

ACCEPT_BUCKETS = (
    (EARLY, "pre_rotation_ok"),
    (MID, "transitional_ok"),
    (LATE, "post_rotation_ok"),
    (DUAL, "dual_attest_ok"),
    (REVOKED, "signer_valid_at_time"),
)
REJECT_BUCKETS = (
    (UNDERWEIGHT, "threshold_shortfall"),
    (SHARD_BOUNDARY, "cross_shard_unattested"),
)


def _run_verify() -> None:
    subprocess.run([str(SCRIPTS / "run-verify.sh")], check=True)


def _rebuild() -> None:
    subprocess.run([str(SCRIPTS / "rebuild-verifier.sh")], check=True)


def _load() -> dict:
    assert VERDICTS.is_file(), "verdicts.json missing"
    return json.loads(VERDICTS.read_text())


def _by_id(report: dict) -> dict[str, dict]:
    return {row["event_id"]: row for row in report["events"]}


def _expected_head() -> int:
    m = 0
    for cp_path in SHARDS_DIR.glob("*/checkpoints/*.json"):
        m = max(m, int(json.loads(cp_path.read_text())["epoch"]))
    return m


def _all_event_ids() -> set[str]:
    return {p.stem for p in EVENTS_DIR.glob("e*.json")}


def _refresh() -> dict:
    _run_verify()
    return _load()


class TestOutputs:
    def test_shape_schema(self):
        """Report schema, checkpoint_head, exact event set, and reason enum."""
        report = _refresh()
        assert set(report.keys()) == {"schema_version", "checkpoint_head", "events"}
        assert report["schema_version"] == 1
        assert report["checkpoint_head"] == _expected_head()
        rows = report["events"]
        assert isinstance(rows, list)
        ids = [row["event_id"] for row in rows]
        assert ids == sorted(ids), "events must be sorted by event_id"
        assert set(ids) == _all_event_ids()
        for row in rows:
            assert set(row.keys()) == {"event_id", "decision", "reason"}
            if row["decision"] == "accept":
                assert row["reason"] in ACCEPT_REASONS
            elif row["decision"] == "reject":
                assert row["reason"] in REJECT_REASONS
            else:
                raise AssertionError(f"bad decision {row['decision']}")

    def test_early_pre_rotation(self):
        """Entries signed before the rotation must admit under their contemporaneous quorum."""
        by = _by_id(_refresh())
        ids, expected_reason = ACCEPT_BUCKETS[0]
        for eid in ids:
            row = by[eid]
            assert row["decision"] == "accept", f"{eid} decision={row['decision']}"
            assert row["reason"] == expected_reason, f"{eid} reason={row['reason']}"

    def test_mid_transitional_window(self):
        """Entries signed inside the rotation transition window must admit."""
        by = _by_id(_refresh())
        ids, expected_reason = ACCEPT_BUCKETS[1]
        for eid in ids:
            row = by[eid]
            assert row["decision"] == "accept", f"{eid} decision={row['decision']}"
            assert row["reason"] == expected_reason, f"{eid} reason={row['reason']}"

    def test_late_post_rotation(self):
        """Entries fully inside the new quorum window admit under it."""
        by = _by_id(_refresh())
        ids, expected_reason = ACCEPT_BUCKETS[2]
        for eid in ids:
            row = by[eid]
            assert row["decision"] == "accept", f"{eid} decision={row['decision']}"
            assert row["reason"] == expected_reason, f"{eid} reason={row['reason']}"

    def test_dual_signed(self):
        """Dual-signed entries admit when either attestation meets its contemporaneous threshold."""
        by = _by_id(_refresh())
        ids, expected_reason = ACCEPT_BUCKETS[3]
        for eid in ids:
            row = by[eid]
            assert row["decision"] == "accept", f"{eid} decision={row['decision']}"
            assert row["reason"] == expected_reason, f"{eid} reason={row['reason']}"

    def test_signer_valid_at_time(self):
        """Cosigners revoked after signing time must remain counted for that entry."""
        by = _by_id(_refresh())
        ids, expected_reason = ACCEPT_BUCKETS[4]
        for eid in ids:
            row = by[eid]
            assert row["decision"] == "accept", f"{eid} decision={row['decision']}"
            assert row["reason"] == expected_reason, f"{eid} reason={row['reason']}"

    def test_underweight_rejects(self):
        """Attestations that never met the contemporaneous threshold must refuse."""
        by = _by_id(_refresh())
        ids, expected_reason = REJECT_BUCKETS[0]
        for eid in ids:
            row = by[eid]
            assert row["decision"] == "reject", f"{eid} decision={row['decision']}"
            assert row["reason"] == expected_reason, f"{eid} reason={row['reason']}"

    def test_shard_boundary_rejects(self):
        """Pre-merge cross-shard references must refuse without cross attestation."""
        by = _by_id(_refresh())
        ids, expected_reason = REJECT_BUCKETS[1]
        for eid in ids:
            row = by[eid]
            assert row["decision"] == "reject", f"{eid} decision={row['decision']}"
            assert row["reason"] == expected_reason, f"{eid} reason={row['reason']}"

    def test_replay_determinism(self):
        """Running the verifier twice in a row must produce identical decisions."""
        first = _refresh()
        second = _refresh()
        first_rows = {r["event_id"]: (r["decision"], r["reason"]) for r in first["events"]}
        second_rows = {r["event_id"]: (r["decision"], r["reason"]) for r in second["events"]}
        assert first_rows == second_rows
        assert first["checkpoint_head"] == second["checkpoint_head"]

    def test_rebuild_parity(self):
        """Rebuilding the binary from current sources must not change any decision."""
        first = _refresh()
        _rebuild()
        second = _refresh()
        first_rows = {r["event_id"]: (r["decision"], r["reason"]) for r in first["events"]}
        second_rows = {r["event_id"]: (r["decision"], r["reason"]) for r in second["events"]}
        assert first_rows == second_rows

    def test_fixtures_intact(self):
        """Fixture trees under /data must not be rewritten by the solver."""
        # Ceremony ledger sanity: two rotations, non-empty members, positive threshold.
        led = json.loads((DATA / "ceremony" / "ledger.json").read_text())
        assert len(led["rotations"]) == 2
        for rot in led["rotations"]:
            assert rot["members"], "rotation members empty"
            assert rot["threshold"] > 0
        # Every event id under /data/events resolves.
        assert _all_event_ids() == (
            EARLY | MID | LATE | DUAL | REVOKED | UNDERWEIGHT | SHARD_BOUNDARY
        )
        # Shards intact.
        assert (SHARDS_DIR / "alpha" / "checkpoints" / "cp_a_merged.json").is_file()
        assert (SHARDS_DIR / "beta" / "checkpoints" / "cp_b_merged.json").is_file()
