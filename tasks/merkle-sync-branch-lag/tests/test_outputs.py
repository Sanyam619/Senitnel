import json
import subprocess
from pathlib import Path

LANE = "/app/bin/lane"
DIGEST_LAB = "/app/ops/scripts/digest_lab.py"
REPORT_PATH = Path("/output/sync-report.json")
DATA = Path("/app/data")
CFG = Path("/app/config/l7")


def _journal_head() -> int:
    head = 0
    for path in sorted((DATA / "journal").glob("tier_*.jsonl")):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            head = max(head, int(rec["gen"]))
    return head


def _expected(branch: int) -> dict:
    raw = subprocess.run(
        ["python3", DIGEST_LAB, str(branch)],
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


def test_fixture_leaf_alpha():
    """Primary leaf resolves to fixture-derived digest at promoted branch."""
    branch = _journal_head()
    expected = _expected(branch)
    report = json.loads(REPORT_PATH.read_text())
    assert report["leaves"]["alpha"] == expected["leaves"]["alpha"]


def test_fixture_leaf_gamma():
    """Branch-two leaf payload digest matches fixture expectations."""
    branch = _journal_head()
    expected = _expected(branch)
    report = json.loads(REPORT_PATH.read_text())
    assert report["leaves"]["gamma"] == expected["leaves"]["gamma"]


def test_fixture_leaf_beta():
    """Baseline leaf digest matches fixture expectations at the promoted branch."""
    branch = _journal_head()
    expected = _expected(branch)
    report = json.loads(REPORT_PATH.read_text())
    assert report["leaves"]["beta"] == expected["leaves"]["beta"]


def test_visible_leaf_map_complete():
    """Every fixture-visible leaf id appears in the sync report with matching digests."""
    branch = _journal_head()
    expected = _expected(branch)
    report = json.loads(REPORT_PATH.read_text())
    assert set(report["leaves"]) == set(expected["leaves"])
    for leaf_id, digest in expected["leaves"].items():
        assert report["leaves"][leaf_id] == digest


def test_promoted_leaf_present():
    """A leaf introduced only at the promoted head appears in the sync report."""
    branch = _journal_head()
    expected = _expected(branch)
    report = json.loads(REPORT_PATH.read_text())
    assert "delta" in report["leaves"]
    assert report["leaves"]["delta"] == expected["leaves"]["delta"]


def test_root_digest_matches_fixture_tree():
    """Root digest matches fixture-derived merkle root at journal head."""
    branch = _journal_head()
    expected = _expected(branch)
    report = json.loads(REPORT_PATH.read_text())
    assert report["root_digest"] == expected["root_digest"]


def test_branch_gen_matches_journal_head():
    """Report branch generation equals journal-derived head."""
    head = _journal_head()
    report = json.loads(REPORT_PATH.read_text())
    runtime = json.loads((DATA / "state/runtime.json").read_text())
    assert report["branch_gen"] == head
    assert runtime["active_gen"] == head


def test_lane_head_alignment():
    """Lane checkpoint head agrees with sync report generation."""
    report = json.loads(REPORT_PATH.read_text())
    lane_head = int(_run([LANE, "head"]))
    assert lane_head == report["branch_gen"]


def test_config_branch_cap_cleared():
    """Operator branch ceiling matches the promoted journal head."""
    head = _journal_head()
    assert _config_field("branch_cap") == head


def test_runtime_active_matches_head():
    """Runtime active generation matches journal-derived head."""
    runtime = json.loads((DATA / "state/runtime.json").read_text())
    head = _journal_head()
    assert runtime["active_gen"] == head


def test_output_json_schema_valid():
    """Sync report exposes required fields with valid types."""
    assert REPORT_PATH.is_file(), "sync report missing"
    payload = json.loads(REPORT_PATH.read_text())
    assert isinstance(payload.get("branch_gen"), int)
    assert isinstance(payload.get("root_digest"), str)
    leaves = payload.get("leaves")
    assert isinstance(leaves, dict)
    for digest in leaves.values():
        assert isinstance(digest, str)
        int(digest, 16)
