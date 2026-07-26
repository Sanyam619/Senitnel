"""Hard outcome checks for workload SVID trust-mesh cutover."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
REPORT = Path("/output/mesh-cutover.json")
SEED = Path("/app/data/fixtures/seed.json")
RUNTIME = Path("/app/data/state/runtime.json")

EXPECTED = {
    "fresh_ok": {
        "decision": "accept",
        "reason_code": "ok_fresh",
        "handshake": "fresh",
        "trust_epoch": 7,
    },
    "resume_stale": {
        "decision": "reject",
        "reason_code": "ticket_stale",
        "handshake": "resumed",
        "trust_epoch": 7,
    },
    "expired_inter": {
        "decision": "reject",
        "reason_code": "inter_expired",
        "handshake": "fresh",
        "trust_epoch": 7,
    },
    "dual_post": {
        "decision": "reject",
        "reason_code": "root_stale",
        "handshake": "fresh",
        "trust_epoch": 7,
    },
    "spi_bind": {
        "decision": "accept",
        "reason_code": "spi_ok",
        "handshake": "fresh",
        "trust_epoch": 7,
    },
    "skew_early": {
        "decision": "reject",
        "reason_code": "inter_early",
        "handshake": "fresh",
        "trust_epoch": 7,
    },
}


@pytest.fixture(scope="session")
def state() -> dict:
    before = SEED.read_bytes()
    # Verifier re-runs probe against whatever cutover state the agent left.
    subprocess.run([str(APP / "bin/meshctl"), "probe"], cwd=APP, check=True, timeout=600)
    assert REPORT.is_file(), "meshctl did not write /output/mesh-cutover.json"
    data = json.loads(REPORT.read_text(encoding="utf-8"))
    assert data.get("schema_version") == "mesh-cutover-1"
    assert (APP / "m2/out/io/helix/qx/sieve_b.class").is_file()
    assert SEED.read_bytes() == before, "fixtures were altered"
    return data


def _by_id(payload: dict) -> dict[str, dict]:
    rows = payload.get("cases")
    assert isinstance(rows, list)
    out = {}
    for row in rows:
        assert isinstance(row, dict)
        assert "id" in row
        out[row["id"]] = row
    return out


def test_k9_zircon(state: dict) -> None:
    """Fresh peer under post-flip root/generation must accept."""
    row = _by_id(state)["fresh_ok"]
    want = EXPECTED["fresh_ok"]
    assert row["decision"] == want["decision"]
    assert row["reason_code"] == want["reason_code"]
    assert row["handshake"] == want["handshake"]
    assert row["trust_epoch"] == want["trust_epoch"]
    live = json.loads((APP / "data/state/live-bundle.json").read_text(encoding="utf-8"))
    assert live.get("active_root") == "root-b"
    assert live.get("epoch") == 7
    assert live.get("generation") == 2
    assert live.get("kid") == "rb-07"


def test_m2_quartz(state: dict) -> None:
    """Resumed ticket below the raised floor must reject."""
    row = _by_id(state)["resume_stale"]
    want = EXPECTED["resume_stale"]
    assert row["decision"] == want["decision"]
    assert row["reason_code"] == want["reason_code"]
    gate = json.loads((APP / "data/state/ticket-gate.json").read_text(encoding="utf-8"))
    assert gate.get("min_ticket_epoch") == 7


def test_n3_garnet(state: dict) -> None:
    """Expired intermediate must reject once the warm manager cache is rebound."""
    row = _by_id(state)["expired_inter"]
    want = EXPECTED["expired_inter"]
    assert row["decision"] == want["decision"]
    assert row["reason_code"] == want["reason_code"]
    cache = json.loads((APP / "data/state/tm-cache.json").read_text(encoding="utf-8"))
    assert cache.get("warm") is False
    assert cache.get("last_root") == "root-b"
    assert cache.get("last_epoch") == 7


def test_p7_topaz(state: dict) -> None:
    """Pre-flip root peer must reject under the published live root."""
    row = _by_id(state)["dual_post"]
    want = EXPECTED["dual_post"]
    assert row["decision"] == want["decision"]
    assert row["reason_code"] == want["reason_code"]


def test_r8_onyx(state: dict) -> None:
    """Root-scoped SPI subject must accept; legacy global subject is not authority."""
    row = _by_id(state)["spi_bind"]
    want = EXPECTED["spi_bind"]
    assert row["decision"] == want["decision"]
    assert row["reason_code"] == want["reason_code"]
    roots = json.loads((APP / "data/material/roots.json").read_text(encoding="utf-8"))
    assert roots["spi_by_root"]["root-b"] == "spiffe://mesh/svc/alpha"
    assert roots.get("spi_subject") == "spiffe://mesh/svc/legacy"


def test_w4_basalt(state: dict) -> None:
    """Intermediate not_before beyond runtime as_of must reject as inter_early."""
    row = _by_id(state)["skew_early"]
    want = EXPECTED["skew_early"]
    assert row["decision"] == want["decision"]
    assert row["reason_code"] == want["reason_code"]
    runtime = json.loads(RUNTIME.read_text(encoding="utf-8"))
    assert runtime.get("as_of") == 1700000000


def test_t1_amber(state: dict) -> None:
    """Ledger must cover every scenario with runtime epoch; readycheck alone is insufficient."""
    runtime = json.loads(RUNTIME.read_text(encoding="utf-8"))
    assert state.get("epoch") == runtime.get("epoch") == 7
    by_id = _by_id(state)
    assert set(by_id) == set(EXPECTED)
    for case_id, want in EXPECTED.items():
        row = by_id[case_id]
        assert row["decision"] == want["decision"]
        assert row["reason_code"] == want["reason_code"]
        assert row["handshake"] == want["handshake"]
        assert row["trust_epoch"] == want["trust_epoch"]
    ready = subprocess.run(
        [str(APP / "bin/readycheck")],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "OK" in ready.stdout
