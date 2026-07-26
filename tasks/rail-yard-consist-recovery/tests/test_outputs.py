import json
import os
import subprocess
from pathlib import Path

LANE = "/app/bin/lane"
YARDCTL = "/app/bin/yardctl"
CONSIST_LAB = "/app/ops/scripts/consist_lab.py"
REPORT_PATH = Path("/output/consist-report.json")
DATA = Path("/app/data")
CFG = Path("/app/config/l7")
CARS_DIR = DATA / "cars"

EXPECTED_CARS = {
    "C101": {"id": "C101", "kind": "box", "since": 1},
    "C102": {"id": "C102", "kind": "box", "since": 1},
    "C103": {"id": "C103", "kind": "tank", "since": 3},
    "C104": {"id": "C104", "kind": "flat", "since": 6},
    "C105": {"id": "C105", "kind": "hopper", "since": 7},
}


def _movement_head() -> int:
    head = 0
    for path in sorted((DATA / "movements").glob("tier_*.jsonl")):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            head = max(head, int(rec["seq"]))
    return head


def _expected(seq: int) -> dict:
    raw = subprocess.run(
        ["python3", CONSIST_LAB, str(seq)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return json.loads(raw)


def _config_field(field: str):
    for path in sorted(CFG.glob("*.toml")):
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if not stripped.startswith(f"{field} ="):
                continue
            raw = stripped.split("=", 1)[1].strip()
            if raw.startswith('"'):
                return json.loads(raw)
            return int(raw)
    raise AssertionError(f"missing operator table field {field}")


def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def test_rebuilt_binaries_executable():
    """Shipped lane and yardctl binaries are present and executable."""
    for path in (LANE, YARDCTL):
        assert os.path.isfile(path)
        assert os.access(path, os.X_OK)


def test_car_fixtures_unmodified():
    """Car fixture records under /app/data/cars/ remain unmodified."""
    for car_id, expected in EXPECTED_CARS.items():
        payload = json.loads((CARS_DIR / f"{car_id}.json").read_text())
        assert payload == expected


def test_track_t1_lead_car():
    """Lead car on T1 resolves to fixture-derived order at promoted sequence."""
    seq = _movement_head()
    expected = _expected(seq)
    report = json.loads(REPORT_PATH.read_text())
    assert report["tracks"]["T1"][0] == expected["tracks"]["T1"][0]


def test_track_t1_second_car():
    """Second T1 slot matches fixture-derived movement window."""
    seq = _movement_head()
    expected = _expected(seq)
    report = json.loads(REPORT_PATH.read_text())
    assert report["tracks"]["T1"][1] == expected["tracks"]["T1"][1]


def test_track_t1_third_car():
    """Late-arrival car on T1 matches fixture expectations at promoted head."""
    seq = _movement_head()
    expected = _expected(seq)
    report = json.loads(REPORT_PATH.read_text())
    assert report["tracks"]["T1"][2] == expected["tracks"]["T1"][2]


def test_track_map_complete():
    """Every fixture-visible track id appears in the yard report with matching car order."""
    seq = _movement_head()
    expected = _expected(seq)
    report = json.loads(REPORT_PATH.read_text())
    assert set(report["tracks"]) == set(expected["tracks"])
    for track_id, cars in expected["tracks"].items():
        assert report["tracks"][track_id] == cars


def test_promoted_car_on_t1():
    """T1 car count at promoted head exceeds the partial-replay window."""
    seq = _movement_head()
    expected = _expected(seq)
    report = json.loads(REPORT_PATH.read_text())
    assert len(report["tracks"]["T1"]) == len(expected["tracks"]["T1"])
    assert report["tracks"]["T1"] == expected["tracks"]["T1"]


def test_track_t2_tail_car():
    """T2 tail car matches fixture-derived movement window at promoted head."""
    seq = _movement_head()
    expected = _expected(seq)
    report = json.loads(REPORT_PATH.read_text())
    assert report["tracks"]["T2"] == expected["tracks"]["T2"]


def test_track_t3_hopper_car():
    """Hopper staged on the storage track matches fixture expectations at promoted head."""
    seq = _movement_head()
    expected = _expected(seq)
    report = json.loads(REPORT_PATH.read_text())
    assert report["tracks"]["T3"] == expected["tracks"]["T3"]


def test_relocated_tank_not_ghosted_on_departure_spur():
    """Relocated tank id is absent from the departure spur once replay reaches the promoted head."""
    seq = _movement_head()
    report = json.loads(REPORT_PATH.read_text())
    assert report["replay_seq"] == seq
    assert "C103" not in report["tracks"].get("T2", [])


def test_audit_digest_matches_fixture_probe():
    """Audit digest matches fixture-derived consist probe at movement head."""
    seq = _movement_head()
    expected = _expected(seq)
    report = json.loads(REPORT_PATH.read_text())
    assert report["audit_digest"] == expected["audit_digest"]


def test_replay_seq_matches_movement_head():
    """Report replay sequence equals movement-derived head."""
    head = _movement_head()
    report = json.loads(REPORT_PATH.read_text())
    runtime = json.loads((DATA / "state" / "runtime.json").read_text())
    assert report["replay_seq"] == head
    assert runtime["active_seq"] == head


def test_lane_probe_alignment():
    """Lane movement probe agrees with yard report replay sequence."""
    report = json.loads(REPORT_PATH.read_text())
    lane_seq = int(_run([LANE, "probe"]))
    assert lane_seq == report["replay_seq"]


def test_config_journal_pin_cleared():
    """Operator journal pin matches the promoted movement head."""
    head = _movement_head()
    assert _config_field("journal_pin") == head


def test_config_seq_floor_cleared():
    """Operator sequence floor matches the promoted movement head."""
    head = _movement_head()
    assert _config_field("seq_floor") == head


def test_replay_gate_allows_pull_replay():
    """Movement replay gate permits pull operations during consist reconstruction."""
    assert _config_field("replay_gate") == 0


def test_tier_reducer_uses_promoted_head():
    """Movement tier reducer mode selects the promoted head rather than the shallowest tier."""
    assert _config_field("tier_reducer") == "max"


def test_runtime_active_matches_head():
    """Runtime active replay sequence matches movement-derived head."""
    runtime = json.loads((DATA / "state" / "runtime.json").read_text())
    head = _movement_head()
    assert runtime["active_seq"] == head


def test_output_json_schema_valid():
    """Yard report exposes required fields with valid types."""
    assert REPORT_PATH.is_file(), "consist report missing"
    payload = json.loads(REPORT_PATH.read_text())
    assert isinstance(payload.get("replay_seq"), int)
    assert isinstance(payload.get("audit_digest"), str)
    tracks = payload.get("tracks")
    assert isinstance(tracks, dict)
    for cars in tracks.values():
        assert isinstance(cars, list)
        for car in cars:
            assert isinstance(car, str)
    int(payload["audit_digest"], 16)
