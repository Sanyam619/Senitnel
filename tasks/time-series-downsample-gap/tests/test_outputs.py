"""Verifier tests for time-series downsample gap recovery outcomes."""

import json
import subprocess
from pathlib import Path

CTL = "/app/bin/ctl"
REPORT_PATH = Path("/output/rewind-report.json")
RUNTIME_PATH = Path("/app/data/state/runtime.json")
CFG = Path("/app/config/l7")
QUERY_TS = 550
METRICS_TS = 100


def _ctl_json(args: list[str]) -> dict:
    """Run ctl with arguments and parse JSON stdout."""
    result = subprocess.run(
        [CTL, *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout.strip())


def _load_runtime() -> dict:
    return json.loads(RUNTIME_PATH.read_text())


def _config_field(field: str):
    """Read a single field from whichever operator table defines it."""
    for path in sorted(CFG.glob("*.toml")):
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if not stripped.startswith(f"{field} ="):
                continue
            raw = stripped.split("=", 1)[1].strip()
            if raw.startswith("["):
                return json.loads(raw)
            if raw.startswith('"'):
                return json.loads(raw)
            return int(raw)
    raise AssertionError(f"missing operator table field {field}")


def _discover_roll_anchor() -> int:
    """Last events journal generation before the partial-merge stripe appears."""
    anchor = None
    for line in Path("/app/data/manifests/tier_b.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("ns") != "events":
            continue
        if 99 in rec.get("stripes", []):
            break
        anchor = int(rec["gen"])
    if anchor is None:
        raise AssertionError("could not derive roll anchor from tier_b journal")
    return anchor


def _discover_barrier_cutoff() -> tuple[int, str]:
    """WAL sequence and tombstoned key at the barrier cutoff fixture."""
    tombstone_seq = None
    tombstone_key = None
    for name in ("seg_001.bin", "seg_002.bin"):
        blob = (Path("/app/data/wal") / name).read_bytes()
        if blob[:4] != b"WLOG":
            raise AssertionError(f"bad wal magic in {name}")
        off = 4
        while off + 11 <= len(blob):
            seq = int.from_bytes(blob[off : off + 8], "little")
            off += 8
            op = blob[off]
            off += 1
            key_len = int.from_bytes(blob[off : off + 2], "little")
            off += 2
            key = blob[off : off + key_len].decode()
            off += key_len
            off += 8
            if op == 1:
                tombstone_seq = seq
                tombstone_key = key
    if tombstone_seq is None or tombstone_key is None:
        raise AssertionError("could not locate tombstone cutoff in wal segments")
    return tombstone_seq, tombstone_key


def _load_column_record(ns: str, stripe: int, key: str) -> dict:
    """Load a single key payload from a column stripe fixture."""
    path = Path(f"/app/data/columns/{ns}_{stripe:03}.col")
    payload = json.loads(path.read_text())
    for record in payload["records"]:
        if record["k"] == key:
            return record
    raise AssertionError(f"missing {key} in {path}")


def _merged_aggregate(ns: str, ts: int) -> dict:
    """Derive aggregate count and timestamp sum from the merged stripe fixture."""
    path = Path(f"/app/data/columns/{ns}_merged.col")
    rows = [r for r in json.loads(path.read_text())["records"] if r["t"] <= ts]
    return {"count": len(rows), "sum_ts": sum(r["t"] for r in rows)}


def _range_keys(lo: str, hi: str) -> list[str]:
    """Sorted keys from the events merged stripe within an inclusive key window."""
    rows = json.loads(Path("/app/data/columns/events_merged.col").read_text())["records"]
    return sorted(r["k"] for r in rows if lo <= r["k"] <= hi)


def test_fixture_vector_alpha():
    """Primary fixture keys resolve to expected payloads at the query timestamp."""
    alpha = _load_column_record("events", 1, "alpha")
    beta = _load_column_record("events", 1, "beta")
    gamma = _load_column_record("events", 2, "gamma")

    got_alpha = _ctl_json(["query", "point", "--ks", "events", "--key", "alpha", "--ts", str(QUERY_TS)])
    got_beta = _ctl_json(["query", "point", "--ks", "events", "--key", "beta", "--ts", str(QUERY_TS)])
    got_gamma = _ctl_json(["query", "point", "--ks", "events", "--key", "gamma", "--ts", str(QUERY_TS)])

    assert got_alpha["found"] is True
    assert got_alpha["value"] == alpha["v"]
    assert got_alpha["ts"] == alpha["t"]

    assert got_beta["found"] is True
    assert got_beta["value"] == beta["v"]

    assert got_gamma["found"] is True
    assert got_gamma["value"] == gamma["v"]


def test_fixture_vector_beta():
    """Range scan returns keys in sorted order with stable payload values."""
    alpha = _load_column_record("events", 1, "alpha")
    beta = _load_column_record("events", 1, "beta")
    gamma = _load_column_record("events", 2, "gamma")
    expected_keys = _range_keys("alpha", "gamma")

    payload = _ctl_json(
        [
            "query",
            "range",
            "--ks",
            "events",
            "--lo",
            "alpha",
            "--hi",
            "gamma",
            "--ts",
            str(QUERY_TS),
        ]
    )
    keys = [hit["key"] for hit in payload["hits"]]
    assert keys == expected_keys
    values = [hit["value"] for hit in payload["hits"]]
    assert values == [alpha["v"], beta["v"], gamma["v"]]


def test_absent_marker_at_window():
    """Tombstoned fixture key stays absent for the queried time window."""
    cutoff, tombstone_key = _discover_barrier_cutoff()
    payload = _ctl_json(
        ["query", "point", "--ks", "events", "--key", tombstone_key, "--ts", str(QUERY_TS)]
    )
    assert payload["found"] is False
    runtime = _load_runtime()
    assert runtime["tombstone_seq"] == cutoff


def test_aggregate_totals_stable():
    """Namespace aggregate totals match the merged stripe baseline at the query window."""
    expected = _merged_aggregate("events", QUERY_TS)
    payload = _ctl_json(["query", "aggregate", "--ks", "events", "--ts", str(QUERY_TS)])
    assert payload["count"] == expected["count"]
    assert payload["sum_ts"] == expected["sum_ts"]


def test_output_json_schema_valid():
    """Rewind report JSON exposes required fields with valid types and values."""
    assert REPORT_PATH.is_file(), "rewind report missing"
    payload = json.loads(REPORT_PATH.read_text())

    assert isinstance(payload.get("restored_generation"), int)
    for ns in ("events", "metrics"):
        block = payload.get(ns)
        assert isinstance(block, dict)
        assert isinstance(block.get("visible_segments"), int)
        digest = block.get("sidecar_digest")
        assert isinstance(digest, str)
        assert len(digest) >= 16
        int(digest, 16)

    status = _ctl_json(["status"])
    anchor = _discover_roll_anchor()
    assert 0 < payload["restored_generation"] <= status["ceiling_gen"]
    assert payload["restored_generation"] == anchor


def test_chain_order_invariant():
    """Restored journal generation matches rolled runtime state below the ceiling."""
    status = _ctl_json(["status"])
    runtime = _load_runtime()
    payload = json.loads(REPORT_PATH.read_text())
    restored = payload["restored_generation"]
    anchor = _discover_roll_anchor()

    assert 0 < restored <= status["ceiling_gen"]
    assert restored == runtime["active_gen"]
    assert runtime["active_gen"] == anchor
    assert runtime["active_gen"] < status["ceiling_gen"]


def test_barrier_tombstone_runtime_state():
    """Barrier replay committed tombstone state tied to the WAL cutoff fixture."""
    runtime = _load_runtime()
    cutoff, tombstone_key = _discover_barrier_cutoff()

    assert runtime["tombstone_seq"] == cutoff
    assert _config_field("seq_cutoff") == cutoff
    assert runtime["wal_seq"] >= cutoff
    assert tombstone_key in runtime["tombstone_keys"]


def test_recovery_config_phase_order():
    """Operator tables carry corrected anchor, cutoff, and roll-barrier-rebuild ordering."""
    anchor = _discover_roll_anchor()
    cutoff, _tombstone_key = _discover_barrier_cutoff()
    phases = _config_field("phases")

    assert _config_field("tier_c") == anchor
    assert _config_field("seq_cutoff") == cutoff
    roll = phases.index("roll")
    barrier = phases.index("barrier")
    rebuild = phases.index("rebuild")
    assert roll < barrier < rebuild


def test_rebuild_generation_alignment():
    """Rebuilt events sidecar is bound to the rolled generation, not the broken head."""
    runtime = _load_runtime()
    anchor = _discover_roll_anchor()
    _cutoff, tombstone_key = _discover_barrier_cutoff()
    sidecar = json.loads(Path("/app/data/sidecars/events.idx").read_text())

    assert runtime["active_gen"] == anchor
    assert sidecar["bound_gen"] == anchor
    assert runtime["sidecar_gen"]["events"] == anchor
    assert tombstone_key not in sidecar["map"]


def test_digest_checksum_match():
    """Rebuilt sidecar digest on disk matches the rewind report entry."""
    runtime = _load_runtime()
    assert runtime["active_gen"] == _discover_roll_anchor()
    payload = json.loads(REPORT_PATH.read_text())
    events_digest = payload["events"]["sidecar_digest"]
    sidecar = json.loads(Path("/app/data/sidecars/events.idx").read_text())
    assert sidecar["digest"] == events_digest


def test_secondary_namespace_stable():
    """Unaffected namespace probes and digest remain at baseline expectations."""
    m1 = _load_column_record("metrics", 10, "m1")
    expected_agg = _merged_aggregate("metrics", METRICS_TS)

    point = _ctl_json(["query", "point", "--ks", "metrics", "--key", "m1", "--ts", str(METRICS_TS)])
    agg = _ctl_json(["query", "aggregate", "--ks", "metrics", "--ts", str(METRICS_TS)])

    assert point["found"] is True
    assert point["key"] == m1["k"]
    assert point["value"] == m1["v"]
    assert point["ts"] == m1["t"]

    assert agg["count"] == expected_agg["count"]
    assert agg["sum_ts"] == expected_agg["sum_ts"]

    report = json.loads(REPORT_PATH.read_text())
    metrics_sidecar = json.loads(Path("/app/data/sidecars/metrics.idx").read_text())
    assert report["metrics"]["sidecar_digest"] == metrics_sidecar["digest"]
