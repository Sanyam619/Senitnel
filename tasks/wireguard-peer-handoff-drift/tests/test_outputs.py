"""Verifier tests for WireGuard peer handoff reconcile output."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

OPT = Path("/opt/wghandoff")
OUT = Path("/output")
RECONCILE = OPT / "bin" / "reconcile"
SCENARIO_ROOT = OPT / "data" / "scenarios"
BUNDLE_INDEX = SCENARIO_ROOT / "bundle_index.json"
REPORT_PATH = OUT / "handoff_report.json"


def load_bundle_index():
    return json.loads(BUNDLE_INDEX.read_text(encoding="utf-8"))["bundles"]


def load_manifest(node_id: str) -> dict:
    return json.loads(
        (SCENARIO_ROOT / node_id / "manifest.json").read_text(encoding="utf-8")
    )


def load_epoch_table(node_id: str) -> dict:
    return json.loads(
        (SCENARIO_ROOT / node_id / "epoch_table.json").read_text(encoding="utf-8")
    )


def target_member_ids(node_id: str) -> list[str]:
    manifest = load_manifest(node_id)
    table = load_epoch_table(node_id)
    target = manifest["target_epoch"]
    active = []
    for row in table["epochs"]:
        if row["epoch"] == target:
            active = sorted(m["id"] for m in row["members"])
    return active


def prior_retired_ids(node_id: str) -> set[str]:
    manifest = load_manifest(node_id)
    table = load_epoch_table(node_id)
    target = manifest["target_epoch"]
    target_set = set(target_member_ids(node_id))
    prior = set()
    for row in table["epochs"]:
        if row["epoch"] < target:
            for m in row["members"]:
                prior.add(m["id"])
    return prior - target_set


def expected_node_row(node_id: str) -> dict:
    manifest = load_manifest(node_id)
    return {
        "node_id": node_id,
        "epoch": manifest["target_epoch"],
        "active_ids": target_member_ids(node_id),
        "drift": 0,
        "clean": True,
    }


def expected_report() -> dict:
    nodes = [expected_node_row(node_id) for node_id in sorted(load_bundle_index())]
    return {"version": 1, "nodes": nodes, "drifts": []}


def run_tool():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    subprocess.run(
        ["go", "build", "-o", "bin/reconcile", "./cmd/reconcile"],
        check=True,
        cwd=OPT,
        timeout=120,
    )
    subprocess.run(
        [
            str(RECONCILE),
            "--policy",
            str(OPT / "data" / "policy.toml"),
            "--scenarios",
            str(OPT / "data" / "scenarios"),
            "--out",
            str(OUT),
        ],
        check=True,
        cwd=OPT,
        timeout=120,
    )
    return json.loads(REPORT_PATH.read_text())


@pytest.fixture(scope="module")
def report():
    return run_tool()


def test_report_exists(report):
    """handoff_report.json is written to the instructed output path."""
    assert REPORT_PATH.is_file()
    assert report["version"] == 1


def test_report_trailing_newline(report):
    """Report file ends with a single trailing newline."""
    raw = REPORT_PATH.read_bytes()
    assert raw.endswith(b"\n")
    assert not raw.endswith(b"\n\n")


def test_bundle_count(report):
    """Report row count matches the bundle index fleet size."""
    assert len(report["nodes"]) == len(load_bundle_index())


def test_all_nodes_present(report):
    """Report covers every scenario bundle."""
    expected = set(load_bundle_index())
    assert {r["node_id"] for r in report["nodes"]} == expected


def test_nodes_sorted(report):
    """Node rows appear in ascending node_id order."""
    ids = [row["node_id"] for row in report["nodes"]]
    assert ids == sorted(ids)


def test_active_ids_sorted(report):
    """Each node lists active_ids in ascending order."""
    for row in report["nodes"]:
        assert row["active_ids"] == sorted(row["active_ids"])


def test_all_nodes_zero_drift(report):
    """Every node reports zero membership drift after reconcile."""
    assert all(row["drift"] == 0 for row in report["nodes"])


def test_all_nodes_clean(report):
    """Every node reports clean true after reconcile."""
    assert all(row["clean"] is True for row in report["nodes"])


def test_epoch_matches_manifest_target(report):
    """Each node epoch field matches its manifest target_epoch."""
    for row in report["nodes"]:
        manifest = load_manifest(row["node_id"])
        assert row["epoch"] == manifest["target_epoch"]


def test_active_ids_match_target_epoch_row(report):
    """active_ids equals the target epoch roster from epoch_table.json."""
    for row in report["nodes"]:
        assert row["active_ids"] == target_member_ids(row["node_id"])


def test_no_retired_peer_on_wire(report):
    """Superseded peers from earlier epochs do not survive on the wire."""
    for row in report["nodes"]:
        stale = prior_retired_ids(row["node_id"])
        live = set(row["active_ids"])
        assert live.isdisjoint(stale)


def test_alpha_epoch(report):
    """Alpha reaches target epoch three with only m-a4 and m-a5 live."""
    row = next(r for r in report["nodes"] if r["node_id"] == "alpha")
    assert row == expected_node_row("alpha")


def test_bravo_clean(report):
    """Bravo finishes on epoch two with sole member m-b3."""
    row = next(r for r in report["nodes"] if r["node_id"] == "bravo")
    assert row == expected_node_row("bravo")


def test_charlie_members(report):
    """Charlie lands epoch four with m-c4 and m-c5 only."""
    row = next(r for r in report["nodes"] if r["node_id"] == "charlie")
    assert row == expected_node_row("charlie")


def test_delta_no_stale(report):
    """Delta drops retired m-d1 and keeps m-d2 and m-d3."""
    row = next(r for r in report["nodes"] if r["node_id"] == "delta")
    assert row == expected_node_row("delta")


def test_echo_pending_lag(report):
    """Echo reaches epoch four despite a stale pending queue epoch label."""
    row = next(r for r in report["nodes"] if r["node_id"] == "echo")
    assert row == expected_node_row("echo")
    pending = json.loads(
        (SCENARIO_ROOT / "echo" / "pending.json").read_text(encoding="utf-8")
    )
    manifest = load_manifest("echo")
    assert pending["epoch"] != manifest["target_epoch"]


def test_foxtrot_queue_roster_mismatch(report):
    """Foxtrot promotes epoch-three roster m-f3 and m-f4, not the queued epoch-two peer."""
    row = next(r for r in report["nodes"] if r["node_id"] == "foxtrot")
    assert row == expected_node_row("foxtrot")
    pending = json.loads(
        (SCENARIO_ROOT / "foxtrot" / "pending.json").read_text(encoding="utf-8")
    )
    assert pending["epoch"] == load_manifest("foxtrot")["target_epoch"]
    assert pending["member_ids"] != row["active_ids"]


def test_golf_cidr_reuse(report):
    """Golf reuses retired AllowedIPs 10.70.1.0/24 on m-g3 at epoch three."""
    row = next(r for r in report["nodes"] if r["node_id"] == "golf")
    assert row == expected_node_row("golf")
    table = load_epoch_table("golf")
    prior_cidrs = set()
    for erow in table["epochs"]:
        if erow["epoch"] < 3:
            for m in erow["members"]:
                prior_cidrs.update(m["allowed_ips"])
    target_cidrs = set()
    for erow in table["epochs"]:
        if erow["epoch"] == 3:
            for m in erow["members"]:
                target_cidrs.update(m["allowed_ips"])
    assert prior_cidrs & target_cidrs
    assert "m-g3" in row["active_ids"]
    assert "m-g4" in row["active_ids"]


def test_hotel_carry_forward(report):
    """Hotel keeps carry-forward peer m-h2 while retiring m-h3."""
    row = next(r for r in report["nodes"] if r["node_id"] == "hotel")
    assert row == expected_node_row("hotel")
    assert row["active_ids"] == ["m-h2", "m-h4"]
    table = load_epoch_table("hotel")
    ep2 = next(r["members"] for r in table["epochs"] if r["epoch"] == 2)
    ep3 = next(r["members"] for r in table["epochs"] if r["epoch"] == 3)
    assert {m["id"] for m in ep2} & {m["id"] for m in ep3} == {"m-h2"}


def test_carry_forward_not_treated_as_retired(report):
    """Peers present in both prior and target epochs remain on the wire."""
    for node_id in load_bundle_index():
        target = set(target_member_ids(node_id))
        table = load_epoch_table(node_id)
        manifest = load_manifest(node_id)
        prior = set()
        for erow in table["epochs"]:
            if erow["epoch"] < manifest["target_epoch"]:
                prior.update(m["id"] for m in erow["members"])
        carry = prior & target
        if not carry:
            continue
        row = next(r for r in report["nodes"] if r["node_id"] == node_id)
        assert carry.issubset(set(row["active_ids"]))


def test_policy_cutover_knobs_intact():
    """Cutover policy knobs remain the lab defaults."""
    text = (OPT / "data" / "policy.toml").read_text(encoding="utf-8")
    assert 'epoch_authority = "manifest"' in text
    assert 'roster_source = "epoch_table"' in text
    assert 'staging_mode = "replace"' in text
    assert "allow_cidr_reuse = true" in text


def test_drifts_empty(report):
    """No stale members remain after reconcile."""
    assert report["drifts"] == []


def test_full_report(report):
    """Aggregate report matches scenario-derived expectations."""
    assert report == expected_report()


def test_scenario_fixtures_intact():
    """Bundled scenario manifests match the lab bundle index."""
    index = load_bundle_index()
    assert set(index) == set(index.keys())
    for node_id, meta in index.items():
        manifest = load_manifest(node_id)
        assert manifest["node_id"] == node_id
        assert manifest["target_epoch"] == meta["target_epoch"]


def test_pending_files_unmodified():
    """Verifier does not rewrite automation queue fixtures."""
    for node_id in load_bundle_index():
        pending_path = SCENARIO_ROOT / node_id / "pending.json"
        before = pending_path.read_text(encoding="utf-8")
        run_tool()
        after = pending_path.read_text(encoding="utf-8")
        assert before == after


def test_determinism():
    """Back-to-back runs produce identical JSON."""
    first = run_tool()
    second = run_tool()
    assert first == second
