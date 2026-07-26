"""Verifier for Falco threshold ledger report."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
OUT = APP / "output" / "falco_threshold_report.json"
RUN_CMD = ["/app/bin/frtl_audit"]
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

PACK_ORDER = [
    "clean_alert",
    "priority_pick",
    "rate_burst",
    "suppression_hot",
    "suppression_cold",
    "scope_hit",
    "scope_miss",
    "batch_skew",
    "floor_edge",
    "twin_pid",
    "mute_edge",
    "seq_plateau",
    "rate_edge",
    "tie_lex",
]
EXPECTED = json.loads(
    '{"clean_alert":{"batch_id":"clean_alert","alert_count":1,"suppression_rows":[],"scope_row":{"container_id":"prod-api-1","scope_match":true,"labels_matched":["env=prod"]},"rate_ok":true,"batch_order_ok":true,"winning_priority":70,"effective_rate_window_sec":60,"priority_floor":40,"digest_hex":"d5a418e274ab83249c7d2b6c73569ed7bd8fd2a54c7dbbfd95fde0d9f0d0235c"},"priority_pick":{"batch_id":"priority_pick","alert_count":1,"suppression_rows":[],"scope_row":{"container_id":"prod-web-2","scope_match":true,"labels_matched":["env=prod"]},"rate_ok":true,"batch_order_ok":true,"winning_priority":80,"effective_rate_window_sec":60,"priority_floor":40,"digest_hex":"69f28ae8677dc4b64fd8dc54fe1bc8afe3c56dea76baa59602a3b9bb5e77b2d7"},"rate_burst":{"batch_id":"rate_burst","alert_count":2,"suppression_rows":[],"scope_row":{"container_id":"prod-db-1","scope_match":true,"labels_matched":["env=prod"]},"rate_ok":false,"batch_order_ok":true,"winning_priority":80,"effective_rate_window_sec":60,"priority_floor":40,"digest_hex":"f54c9dffc9d66f58d966aa620e9a5c9c1467302d0a61217653464400803613ec"},"suppression_hot":{"batch_id":"suppression_hot","alert_count":1,"suppression_rows":[{"rule":"file_audit","container_id":"prod-cache-1","pid":400,"bound":true,"reason":"inside-mute"}],"scope_row":{"container_id":"prod-cache-1","scope_match":true,"labels_matched":["env=prod"]},"rate_ok":true,"batch_order_ok":true,"winning_priority":60,"effective_rate_window_sec":60,"priority_floor":40,"digest_hex":"905bcb15cc14d30a0fc308c7d9080fe05104f72616a03e971f101505ae1de493"},"suppression_cold":{"batch_id":"suppression_cold","alert_count":2,"suppression_rows":[],"scope_row":{"container_id":"prod-cache-2","scope_match":true,"labels_matched":["env=prod"]},"rate_ok":true,"batch_order_ok":true,"winning_priority":60,"effective_rate_window_sec":60,"priority_floor":40,"digest_hex":"7e6508485edca9783386f96e87c3210f74f5cfee489a78d5945b838cf9405a72"},"scope_hit":{"batch_id":"scope_hit","alert_count":1,"suppression_rows":[],"scope_row":{"container_id":"prod-worker-3","scope_match":true,"labels_matched":["env=prod"]},"rate_ok":true,"batch_order_ok":true,"winning_priority":70,"effective_rate_window_sec":60,"priority_floor":40,"digest_hex":"b277985d78ce6d15ad314ca535fb9c5ed19aae5b3e2d33eda463952b727f074f"},"scope_miss":{"batch_id":"scope_miss","alert_count":0,"suppression_rows":[],"scope_row":{"container_id":"dev-worker-1","scope_match":false,"labels_matched":[]},"rate_ok":true,"batch_order_ok":true,"winning_priority":0,"effective_rate_window_sec":60,"priority_floor":40,"digest_hex":"faec8981432e63c46cb58ce4edb68cb76c347de035364fec0f6a801db7453ae8"},"batch_skew":{"batch_id":"batch_skew","alert_count":0,"suppression_rows":[],"scope_row":{"container_id":"prod-api-9","scope_match":false,"labels_matched":[]},"rate_ok":false,"batch_order_ok":false,"winning_priority":0,"effective_rate_window_sec":60,"priority_floor":40,"digest_hex":"c537217cd4d798ba7b22f4030b3106d4966a6dac8ca7e2d76ddbc31ee0b27cbb"},"floor_edge":{"batch_id":"floor_edge","alert_count":1,"suppression_rows":[],"scope_row":{"container_id":"prod-edge-1","scope_match":true,"labels_matched":["env=prod"]},"rate_ok":true,"batch_order_ok":true,"winning_priority":40,"effective_rate_window_sec":60,"priority_floor":40,"digest_hex":"0fbf829a179d11f4677840a9f453cada617de71a67f0c7400c0a9f41efcdd7a0"},"twin_pid":{"batch_id":"twin_pid","alert_count":2,"suppression_rows":[],"scope_row":{"container_id":"prod-twin-1","scope_match":true,"labels_matched":["env=prod"]},"rate_ok":true,"batch_order_ok":true,"winning_priority":60,"effective_rate_window_sec":60,"priority_floor":40,"digest_hex":"74c09dab51233f9c02236b86ff3a194f2905b51ae79c06b1762dcee014ba1f6a"},"mute_edge":{"batch_id":"mute_edge","alert_count":2,"suppression_rows":[],"scope_row":{"container_id":"prod-mute-1","scope_match":true,"labels_matched":["env=prod"]},"rate_ok":true,"batch_order_ok":true,"winning_priority":60,"effective_rate_window_sec":60,"priority_floor":40,"digest_hex":"db075719e6b9c863dfa868ce1ffa2b8fe2a31072adca6da886f0255d4673af4f"},"seq_plateau":{"batch_id":"seq_plateau","alert_count":0,"suppression_rows":[],"scope_row":{"container_id":"prod-plat-1","scope_match":false,"labels_matched":[]},"rate_ok":false,"batch_order_ok":false,"winning_priority":0,"effective_rate_window_sec":60,"priority_floor":40,"digest_hex":"917752b6155f84d9b517a362a12529aeb67331b56e0d80ed133f18ae7083cc0e"},"rate_edge":{"batch_id":"rate_edge","alert_count":2,"suppression_rows":[],"scope_row":{"container_id":"prod-edge-r","scope_match":true,"labels_matched":["env=prod"]},"rate_ok":false,"batch_order_ok":true,"winning_priority":80,"effective_rate_window_sec":60,"priority_floor":40,"digest_hex":"1b39054213dbbdc844f3a9cf0cb37b6fa3fe51250fa8b7e99cf77a2dfd8db209"},"tie_lex":{"batch_id":"tie_lex","alert_count":1,"suppression_rows":[{"rule":"file_audit","container_id":"prod-tie-1","pid":140,"bound":true,"reason":"inside-mute"}],"scope_row":{"container_id":"prod-tie-1","scope_match":true,"labels_matched":["env=prod"]},"rate_ok":true,"batch_order_ok":true,"winning_priority":60,"effective_rate_window_sec":60,"priority_floor":40,"digest_hex":"cb3ed32c4fabdad254616f754122121221ea07c1a1941702fd28aa70d76b3810"}}'
)


def _pack_order() -> list[str]:
    return list(PACK_ORDER)


def _run_audit() -> None:
    if OUT.exists():
        OUT.unlink()
    subprocess.run(
        [
            *RUN_CMD,
            "audit",
            "--pack",
            "/app/config/default_pack.json",
            "--out",
            str(OUT),
        ],
        check=True,
        cwd=APP,
    )


def _load_report() -> dict:
    if not OUT.exists():
        _run_audit()
    return json.loads(OUT.read_text(encoding="utf-8"))


def _by_id(report: dict) -> dict[str, dict]:
    return {r["batch_id"]: r for r in report["audits"]}


@pytest.fixture(scope="module")
def report() -> dict:
    _run_audit()
    return _load_report()


class TestFalcoThresholdReport:
    def test_report_schema_and_order(self, report: dict) -> None:
        """Report lists audits in pack order with matching digest rows."""
        assert "audits" in report and "summary" in report
        names = [r["batch_id"] for r in report["audits"]]
        assert names == _pack_order()
        for row in report["audits"]:
            exp = EXPECTED[row["batch_id"]]
            assert DIGEST_RE.match(row["digest_hex"])
            assert row["digest_hex"] == exp["digest_hex"]
            assert row["effective_rate_window_sec"] == exp["effective_rate_window_sec"]
            assert row["priority_floor"] == exp["priority_floor"]

    def test_clean_alert_batch(self, report: dict) -> None:
        """Single scoped syscall yields one detection row."""
        row = _by_id(report)["clean_alert"]
        assert row["alert_count"] == EXPECTED["clean_alert"]["alert_count"]

    def test_priority_pick_batch(self, report: dict) -> None:
        """Higher priority rule wins when multiple rules match."""
        row = _by_id(report)["priority_pick"]
        assert row["winning_priority"] == EXPECTED["priority_pick"]["winning_priority"]
        assert row["alert_count"] == EXPECTED["priority_pick"]["alert_count"]

    def test_rate_burst_batch(self, report: dict) -> None:
        """Per-rule cap trims third alert inside sliding window."""
        row = _by_id(report)["rate_burst"]
        assert row["alert_count"] == EXPECTED["rate_burst"]["alert_count"]
        assert row["rate_ok"] == EXPECTED["rate_burst"]["rate_ok"]

    def test_suppression_hot_batch(self, report: dict) -> None:
        """Duplicate inside mute window records inside-mute suppression row."""
        row = _by_id(report)["suppression_hot"]
        assert row["alert_count"] == EXPECTED["suppression_hot"]["alert_count"]
        assert row["suppression_rows"] == EXPECTED["suppression_hot"]["suppression_rows"]

    def test_suppression_cold_batch(self, report: dict) -> None:
        """Gap beyond mute span allows second alert without suppression rows."""
        row = _by_id(report)["suppression_cold"]
        assert row["alert_count"] == EXPECTED["suppression_cold"]["alert_count"]
        assert row["suppression_rows"] == EXPECTED["suppression_cold"]["suppression_rows"]

    def test_scope_hit_batch(self, report: dict) -> None:
        """Prod prefix container passes scope membership."""
        row = _by_id(report)["scope_hit"]
        assert row["scope_row"]["scope_match"] == EXPECTED["scope_hit"]["scope_row"]["scope_match"]
        assert row["scope_row"]["labels_matched"] == EXPECTED["scope_hit"]["scope_row"]["labels_matched"]
        assert row["alert_count"] == EXPECTED["scope_hit"]["alert_count"]

    def test_scope_miss_batch(self, report: dict) -> None:
        """Dev container outside prod prefix emits zero alerts with scope mismatch."""
        row = _by_id(report)["scope_miss"]
        assert row["alert_count"] == EXPECTED["scope_miss"]["alert_count"]
        assert row["scope_row"]["scope_match"] == EXPECTED["scope_miss"]["scope_row"]["scope_match"]
        assert row["scope_row"]["labels_matched"] == EXPECTED["scope_miss"]["scope_row"]["labels_matched"]

    def test_batch_skew_batch(self, report: dict) -> None:
        """Non-monotonic seq aborts batch with zero alerts."""
        row = _by_id(report)["batch_skew"]
        assert row["batch_order_ok"] is False
        assert row["alert_count"] == 0
        assert row["rate_ok"] == EXPECTED["batch_skew"]["rate_ok"]

    def test_floor_edge_batch(self, report: dict) -> None:
        """Rule priority equal to priority_floor still participates."""
        row = _by_id(report)["floor_edge"]
        assert row["winning_priority"] == EXPECTED["floor_edge"]["winning_priority"]
        assert row["alert_count"] == EXPECTED["floor_edge"]["alert_count"]

    def test_twin_pid_batch(self, report: dict) -> None:
        """Distinct pids on the same container do not share a mute slot."""
        row = _by_id(report)["twin_pid"]
        assert row["alert_count"] == EXPECTED["twin_pid"]["alert_count"]
        assert row["suppression_rows"] == EXPECTED["twin_pid"]["suppression_rows"]

    def test_mute_edge_batch(self, report: dict) -> None:
        """Event landing exactly on the mute span boundary is not suppressed."""
        row = _by_id(report)["mute_edge"]
        assert row["alert_count"] == EXPECTED["mute_edge"]["alert_count"]
        assert row["suppression_rows"] == EXPECTED["mute_edge"]["suppression_rows"]

    def test_seq_plateau_batch(self, report: dict) -> None:
        """Equal consecutive seq values fail the strict order guard."""
        row = _by_id(report)["seq_plateau"]
        assert row["batch_order_ok"] is False
        assert row["alert_count"] == 0
        assert row["rate_ok"] is False

    def test_rate_edge_batch(self, report: dict) -> None:
        """Timestamp exactly one window wide still counts toward the rate cap."""
        row = _by_id(report)["rate_edge"]
        assert row["alert_count"] == EXPECTED["rate_edge"]["alert_count"]
        assert row["rate_ok"] == EXPECTED["rate_edge"]["rate_ok"]

    def test_tie_lex_batch(self, report: dict) -> None:
        """Equal-priority rules break ties by ascending rule name."""
        row = _by_id(report)["tie_lex"]
        assert row["alert_count"] == EXPECTED["tie_lex"]["alert_count"]
        assert row["suppression_rows"] == EXPECTED["tie_lex"]["suppression_rows"]

    def test_summary_guard(self, report: dict) -> None:
        """Summary pack_ok when every batch clears guard expectations."""
        summary = report["summary"]
        assert summary["audited_count"] == len(PACK_ORDER)
        assert summary["pack_ok"] is True

    def test_deterministic_bytes(self) -> None:
        """Two default-pack audit runs yield identical report bytes."""
        _run_audit()
        first = OUT.read_bytes()
        _run_audit()
        second = OUT.read_bytes()
        assert first == second
