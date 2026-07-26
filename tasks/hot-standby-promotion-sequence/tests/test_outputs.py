"""Verifier tests for hot-standby promotion sequence outcomes."""

import json
import subprocess
from pathlib import Path

LIVE_DB = Path("/data/standby/live.db")
TRACE_JSON = Path("/data/standby/elevation_audit.json")
SNAPSHOT_DB = Path("/data/fixtures/snapshot/source.db")
REPLICA_DB = Path("/data/standby/replica.db")
LIVE_SHM = Path("/data/standby/live.db-shm")
LIVE_WAL = Path("/data/standby/live.db-wal")

EXPECTED_ROWS = [
    ("ALPHA", 10),
    ("BETA", 20),
    ("DELTA", 40),
    ("EPSLN", 50),
    ("GAMMA", 30),
]


def _query_inventory(db_path: Path) -> list[tuple[str, int]]:
    out = subprocess.check_output(
        [
            "sqlite3",
            str(db_path),
            "SELECT sku, qty FROM inventory ORDER BY sku;",
        ],
        text=True,
    )
    rows: list[tuple[str, int]] = []
    for line in out.strip().splitlines():
        sku, qty = line.split("|")
        rows.append((sku, int(qty)))
    return rows


def _user_version(db_path: Path) -> int:
    out = subprocess.check_output(
        ["sqlite3", str(db_path), "PRAGMA user_version;"],
        text=True,
    )
    return int(out.strip())


def test_k9_row_bundle():
    """Promoted live.db returns golden inventory rows."""
    assert LIVE_DB.exists(), f"missing {LIVE_DB}"
    rows = _query_inventory(LIVE_DB)
    assert rows == sorted(EXPECTED_ROWS), rows


def test_m4_schema_marker():
    """Promoted live.db keeps user_version 42."""
    assert _user_version(LIVE_DB) == 42


def test_p2_trace_fields():
    """Elevation trace JSON matches the documented schema."""
    assert TRACE_JSON.exists(), f"missing {TRACE_JSON}"
    payload = json.loads(TRACE_JSON.read_text(encoding="utf-8"))
    assert payload.get("version") == 1
    steps = payload.get("steps")
    assert isinstance(steps, list) and len(steps) >= 3
    for step in steps:
        assert isinstance(step.get("tool"), str) and step["tool"]
        assert isinstance(step.get("action"), str) and step["action"]


def test_q7_writable_mode():
    """Promoted live.db is writable standalone storage."""
    subprocess.check_call(
        [
            "sqlite3",
            str(LIVE_DB),
            "INSERT INTO inventory(sku, qty) VALUES ('TMPZ', 1);",
        ]
    )
    rows = _query_inventory(LIVE_DB)
    assert ("TMPZ", 1) in rows
    subprocess.check_call(
        ["sqlite3", str(LIVE_DB), "DELETE FROM inventory WHERE sku='TMPZ';"]
    )


def test_s3_seed_preserved():
    """Snapshot seed file still holds only the original three rows."""
    assert SNAPSHOT_DB.exists()
    rows = _query_inventory(SNAPSHOT_DB)
    assert rows == [("ALPHA", 10), ("BETA", 20), ("GAMMA", 30)]
    assert _user_version(SNAPSHOT_DB) == 42


def test_r1_replica_intact():
    """Replica remains queryable with full inventory after promotion."""
    assert REPLICA_DB.exists()
    rows = _query_inventory(REPLICA_DB)
    assert rows == sorted(EXPECTED_ROWS), rows


def test_n2_standalone_sidecars():
    """Promoted live.db has no wal/shm sidecars."""
    assert not LIVE_WAL.exists(), "live.db-wal should not exist for standalone db"
    assert not LIVE_SHM.exists(), "live.db-shm should not exist for standalone db"


def test_j8_journal_mode():
    """Promoted live.db uses delete journal mode (standalone)."""
    out = subprocess.check_output(
        ["sqlite3", str(LIVE_DB), "PRAGMA journal_mode;"],
        text=True,
    )
    assert out.strip().lower() == "delete"
