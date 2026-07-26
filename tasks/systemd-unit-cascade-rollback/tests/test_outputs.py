"""Verifier tests for stack rollback outcomes."""

import json
import subprocess
from pathlib import Path

REPORT = Path("/output/rollback-report.json")
ANCHOR = Path("/data/fixtures/stack-seed")
RUNTIME = Path("/data/stack/runtime")

NAMES = [
    "journal.service",
    "store.service",
    "cache.service",
    "ingress.service",
    "relay.service",
    "stack.target",
]


def _file_sha256(path: Path) -> str:
    result = subprocess.run(
        ["sha256sum", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.split()[0]


def _load_report() -> dict:
    assert REPORT.exists(), f"missing {REPORT}"
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _unit_map(payload: dict) -> dict[str, dict]:
    units = payload.get("units")
    assert isinstance(units, list)
    return {row["name"]: row for row in units if isinstance(row, dict) and "name" in row}


def test_x3_active_bundle():
    """Every listed name reaches active in the rollback report."""
    by_name = _unit_map(_load_report())
    for name in NAMES:
        assert name in by_name, by_name.keys()
        assert by_name[name].get("state") == "active", name


def test_f7_order_chain():
    """Start order respects After dependencies across the stack."""
    by_name = _unit_map(_load_report())
    order = {name: int(by_name[name]["start_order"]) for name in NAMES}
    assert order["journal.service"] < order["store.service"]
    assert order["store.service"] < order["cache.service"]
    assert order["cache.service"] < order["ingress.service"]
    assert order["ingress.service"] < order["stack.target"]
    assert order["relay.service"] < order["stack.target"]


def test_j2_hard_requires():
    """Requires and bind edges populate hard_deps for coupled units."""
    by_name = _unit_map(_load_report())
    assert len(by_name["store.service"].get("hard_deps", [])) >= 1
    assert len(by_name["relay.service"].get("hard_deps", [])) >= 1
    assert by_name["ingress.service"].get("hard_deps"), "ingress.service"


def test_n5_soft_wants():
    """Wants edges stay in soft_deps rather than hard_deps for cache."""
    by_name = _unit_map(_load_report())
    cache_soft = set(by_name["cache.service"].get("soft_deps", []))
    cache_hard = set(by_name["cache.service"].get("hard_deps", []))
    assert cache_soft
    assert not cache_hard or cache_soft.isdisjoint(cache_hard)


def test_p1_shape_bundle():
    """Rollback report JSON matches the documented schema."""
    payload = _load_report()
    assert payload.get("version") == 1
    units = payload.get("units")
    assert isinstance(units, list) and len(units) >= len(NAMES)
    reported = {row.get("name") for row in units if isinstance(row, dict)}
    assert set(NAMES).issubset(reported), reported
    for row in units:
        assert isinstance(row.get("name"), str) and row["name"]
        assert row.get("state") == "active"
        assert isinstance(row.get("start_order"), int)
        assert isinstance(row.get("hard_deps"), list)
        assert isinstance(row.get("soft_deps"), list)


def test_r4_anchor_intact():
    """Anchor seed tree still reflects the pre-cutover snapshot."""
    manifest = ANCHOR / "checksums.sha256"
    assert manifest.is_file(), manifest
    for line in manifest.read_text(encoding="utf-8").splitlines():
        want_hash, rel = line.split(None, 1)
        rel = rel.strip().removeprefix("./")
        path = ANCHOR / rel
        assert path.is_file(), rel
        assert _file_sha256(path) == want_hash, rel


def test_h8_tally_matches_runtime():
    """Ledger fields match on-disk runtime state files."""
    by_name = _unit_map(_load_report())
    for name in NAMES:
        node = RUNTIME / name
        state = (node / "state").read_text(encoding="utf-8").strip()
        order = int((node / "order").read_text(encoding="utf-8").strip())
        hard = [
            ln.strip()
            for ln in (node / "hard_deps").read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        soft = [
            ln.strip()
            for ln in (node / "soft_deps").read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        row = by_name[name]
        assert row["state"] == state, name
        assert row["start_order"] == order, name
        assert row["hard_deps"] == hard, name
        assert row["soft_deps"] == soft, name


def test_k2_depwalk_accepts_graph():
    """Depwalk accepts a reconciled acyclic graph with no unresolved After edges."""
    result = subprocess.run(
        ["/app/scripts/depwalk-wrapper.sh"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "depwalk ok" in result.stdout
