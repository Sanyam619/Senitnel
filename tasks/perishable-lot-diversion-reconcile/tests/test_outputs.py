"""Tests for perishable lot diversion reconcile."""

import csv
import json
import subprocess
from pathlib import Path

REPORT = Path("/output/diversion-report.json")
DATA = Path("/app/data")
CTL = "/app/bin/ctl"
PROBE_TS = "600"


def ctl_json(args):
    return json.loads(
        subprocess.run([CTL, *args], check=True, capture_output=True, text=True).stdout
    )


def rows(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def all_shipments():
    out = []
    for name in ("north.csv", "south.csv", "ambient.csv"):
        out.extend(rows(DATA / "routes" / name))
    return out


def all_sensors():
    out = []
    for name in ("dock_a.csv", "dock_b.csv", "dock_c.csv"):
        out.extend(rows(DATA / "sensors" / name))
    return out


def cold_anchor_batch():
    return (
        max(
            int(r["batch"])
            for r in rows(DATA / "control" / "diversions.csv")
            if r["lane"] == "cold"
        )
        - 1
    )


def spool_highwater():
    return max(int(r["seq"]) for r in all_sensors())


def latest_status_by_lot(window):
    best = {}
    for r in all_sensors():
        seq = int(r["seq"])
        if seq > window:
            continue
        lot = r["lot"]
        if lot not in best or seq >= best[lot][0]:
            best[lot] = (seq, r["status"])
    return {lot: status for lot, (_seq, status) in best.items()}


def hold_cutoff():
    """Smallest cutoff that quarantines every currently held cold lot and no cleared decoys."""
    # Domain rule under test: cutoff is the latest hold seq among lots whose latest
    # status at that seq is still hold (not a later clear).
    candidates = []
    for r in all_sensors():
        if r["status"] == "hold":
            candidates.append(int(r["seq"]))
    for seq in sorted(candidates, reverse=True):
        held = {lot for lot, st in latest_status_by_lot(seq).items() if st == "hold"}
        if held:
            return seq, held
    raise AssertionError("no active hold window")


def expected_visible(lane):
    anchor = cold_anchor_batch()
    cutoff, held = hold_cutoff()
    _ = cutoff
    return sorted(
        r["lot"]
        for r in all_shipments()
        if r["lane"] == lane and int(r["batch"]) <= anchor and r["lot"] not in held
    )


def sidecar(lane):
    return json.loads((DATA / "sidecars" / f"{lane}.idx").read_text())


def test_diversion_report_exists():
    """Recovery must write the diversion report to the output path."""
    assert REPORT.is_file()


def test_report_schema_and_batch_window():
    """Report exposes valid lane blocks and a restored batch below the ceiling."""
    payload = json.loads(REPORT.read_text())
    status = ctl_json(["status"])
    assert isinstance(payload["restored_batch"], int)
    assert payload["restored_batch"] == cold_anchor_batch()
    assert 0 < payload["restored_batch"] <= status["ceiling_batch"]
    for lane in ("cold", "ambient"):
        assert isinstance(payload[lane]["visible_lots"], int)
        int(payload[lane]["sidecar_digest"], 16)


def test_restored_batch_is_lane_local():
    """Cold restore must follow the cold diversion cutover, not ambient diversion batches."""
    ambient_cut = max(
        int(r["batch"])
        for r in rows(DATA / "control" / "diversions.csv")
        if r["lane"] == "ambient"
    )
    payload = json.loads(REPORT.read_text())
    assert payload["restored_batch"] != ambient_cut - 1
    assert payload["restored_batch"] == cold_anchor_batch()


def test_cold_point_and_scan_agreement():
    """Cold point probes and sorted scans at the same timestamp agree on visible lots."""
    scan = ctl_json(
        ["query", "scan", "--lane", "cold", "--lo", "CEDAR-00", "--hi", "ZZZZ-99", "--ts", PROBE_TS]
    )
    scan_lots = [row["lot"] for row in scan["hits"]]
    assert scan_lots == sorted(scan_lots)
    for lot in scan_lots:
        point = ctl_json(["query", "point", "--lane", "cold", "--lot", lot, "--ts", PROBE_TS])
        assert point["found"] is True
    for lot in expected_visible("cold"):
        assert lot in scan_lots


def test_cold_point_queries_after_recovery():
    """Cold point probes keep valid lots visible while excluding diverted lots."""
    glen = next(r for r in all_shipments() if r["lot"] == "GLEN-17")
    present = ctl_json(["query", "point", "--lane", "cold", "--lot", "GLEN-17", "--ts", PROBE_TS])
    diverted = ctl_json(["query", "point", "--lane", "cold", "--lot", "WREN-88", "--ts", PROBE_TS])
    yarrow = ctl_json(["query", "point", "--lane", "cold", "--lot", "YARROW-70", "--ts", PROBE_TS])
    assert present["found"] is True
    assert present["destination"] == glen["destination"]
    assert present["temp_max"] == int(glen["temp_max"])
    assert diverted["found"] is False
    assert yarrow["found"] is False


def test_held_lot_removed_from_runtime_and_service():
    """Active hold lots are committed to runtime and suppressed from point lookup."""
    cutoff, held = hold_cutoff()
    runtime = json.loads((DATA / "state" / "runtime.json").read_text())
    assert runtime["sensor_seq"] == cutoff
    for lot in held:
        assert lot in runtime["hold_lots"]
        point = ctl_json(["query", "point", "--lane", "cold", "--lot", lot, "--ts", PROBE_TS])
        assert point["found"] is False


def test_cleared_hold_decoy_is_not_quarantined():
    """Lots that were held then cleared inside the cutoff window must not stay quarantined."""
    cutoff, held = hold_cutoff()
    runtime = json.loads((DATA / "state" / "runtime.json").read_text())
    assert "MIST-03" not in held
    assert "MIST-03" not in runtime["hold_lots"]
    # Sticky-hold bugs that latch every historical hold also tend to overshoot the cutoff.
    assert runtime["sensor_seq"] == cutoff
    assert runtime["sensor_seq"] != spool_highwater()


def test_hold_cutoff_differs_from_spool_highwater():
    """Hold cutoff committed to runtime must not collapse onto the spool high-water mark."""
    cutoff, _held = hold_cutoff()
    runtime = json.loads((DATA / "state" / "runtime.json").read_text())
    assert cutoff != spool_highwater()
    assert runtime["sensor_seq"] == cutoff
    assert runtime["sensor_seq"] != spool_highwater()
    # Seal only succeeds when high-water tracking stays intact; stale digests mean it never ran.
    assert sidecar("cold")["digest"] != "stale"
    assert sidecar("ambient")["digest"] != "stale"


def test_scan_matches_sidecar_ordering():
    """Cold scans are sorted and match the sealed sidecar membership."""
    expected = expected_visible("cold")
    scan = ctl_json(
        ["query", "scan", "--lane", "cold", "--lo", "CEDAR-00", "--hi", "ZZZZ-99", "--ts", PROBE_TS]
    )
    lots = [row["lot"] for row in scan["hits"]]
    cold_sc = sidecar("cold")
    assert lots == expected
    assert lots == sorted(lots)
    assert cold_sc["lots"] == expected
    assert cold_sc["bound_batch"] == cold_anchor_batch()
    assert "NOVA-22" not in lots
    assert "WREN-88" not in lots


def test_report_digests_match_sidecars():
    """Report lane digests and lot counts match the on-disk sidecars."""
    payload = json.loads(REPORT.read_text())
    for lane in ("cold", "ambient"):
        sc = sidecar(lane)
        assert payload[lane]["sidecar_digest"] == sc["digest"]
        assert payload[lane]["visible_lots"] == len(sc["lots"])
        assert sc["digest"] != "stale"


def test_ambient_lane_stays_stable():
    """Ambient lane queries and sidecar membership remain unchanged by cold recovery."""
    expected = expected_visible("ambient")
    point = ctl_json(["query", "point", "--lane", "ambient", "--lot", "AMBER-10", "--ts", PROBE_TS])
    scan = ctl_json(
        ["query", "scan", "--lane", "ambient", "--lo", "AMBER-00", "--hi", "ZZZZ-99", "--ts", PROBE_TS]
    )
    assert point["found"] is True
    assert [row["lot"] for row in scan["hits"]] == expected
    assert sidecar("ambient")["lots"] == expected
    assert "COPPER-30" in expected


def test_bind_does_not_drop_quarantine_across_rebind():
    """Re-running bind after a successful sweep must preserve hold membership."""
    before = json.loads((DATA / "state" / "runtime.json").read_text())
    assert before["hold_lots"]
    subprocess.run([CTL, "bind"], check=True, capture_output=True, text=True)
    after = json.loads((DATA / "state" / "runtime.json").read_text())
    assert after["hold_lots"] == before["hold_lots"]
    assert after["active_batch"] == before["active_batch"]
