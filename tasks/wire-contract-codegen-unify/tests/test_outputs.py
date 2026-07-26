"""Verifier tests for wire-contract codegen unification."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

REPORT = Path("/output/wire-unify.json")
XLINK = "/app/bin/xlink"
LANEHEALTH = "/app/bin/lanehealth"
IDL = Path("/app/idl")
REGISTRY = Path("/app/data/registry")
LEDGERS = Path("/tests/ledgers")
IDL_LEDGER = LEDGERS / "idl.sha256"
REGISTRY_LEDGER = LEDGERS / "registry.sha256"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_ledger(ledger: Path, root: Path) -> None:
    assert ledger.is_file(), ledger
    for line in ledger.read_text().splitlines():
        if not line.strip():
            continue
        want_hash, rel = line.split(None, 1)
        target = root / rel
        assert target.is_file(), rel
        assert _sha256_file(target) == want_hash, rel


def _load_report() -> dict:
    assert REPORT.is_file(), f"missing report at {REPORT}"
    data = json.loads(REPORT.read_text())
    assert isinstance(data.get("go_rows"), list) and data["go_rows"], "go_rows empty"
    assert isinstance(data.get("rust_rows"), list) and data["rust_rows"], "rust_rows empty"
    assert isinstance(data.get("java_rows"), list) and data["java_rows"], "java_rows empty"
    return data


def _by_slot(rows: list[dict]) -> dict[str, dict]:
    return {r["slot"]: r for r in rows}


def _canon_digest(rows: list[dict]) -> str:
    parts = [
        f"{r['slot']}:{int(r['tag'])}:{r['kind']}:{r['json_key']}"
        for r in rows
    ]
    blob = "|".join(parts)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def test_k3_zircon():
    """Binary field tags agree across go/rust/java for every slot."""
    data = _load_report()
    go_m = _by_slot(data["go_rows"])
    rust_m = _by_slot(data["rust_rows"])
    java_m = _by_slot(data["java_rows"])
    assert set(go_m) == set(rust_m) == set(java_m)
    for slot in go_m:
        assert int(go_m[slot]["tag"]) == int(rust_m[slot]["tag"]) == int(java_m[slot]["tag"])


def test_m8_obsidian():
    """Kind values for oneof-class slots agree across the three arrays."""
    data = _load_report()
    go_m = _by_slot(data["go_rows"])
    rust_m = _by_slot(data["rust_rows"])
    java_m = _by_slot(data["java_rows"])
    assert "beta" in go_m
    assert go_m["beta"]["kind"] == rust_m["beta"]["kind"] == java_m["beta"]["kind"]
    assert go_m["beta"]["kind"] == "oneof"


def test_p2_garnet():
    """Optional-presence kind agrees for gamma across the three arrays."""
    data = _load_report()
    go_m = _by_slot(data["go_rows"])
    rust_m = _by_slot(data["rust_rows"])
    java_m = _by_slot(data["java_rows"])
    assert "gamma" in go_m
    assert go_m["gamma"]["kind"] == rust_m["gamma"]["kind"] == java_m["gamma"]["kind"]
    assert go_m["gamma"]["kind"] == "optional"


def test_q7_topaz():
    """json_key values agree across languages for every slot."""
    data = _load_report()
    go_m = _by_slot(data["go_rows"])
    rust_m = _by_slot(data["rust_rows"])
    java_m = _by_slot(data["java_rows"])
    assert set(go_m) == set(rust_m) == set(java_m)
    for slot in go_m:
        assert go_m[slot]["json_key"] == rust_m[slot]["json_key"] == java_m[slot]["json_key"]


def test_r1_onyx():
    """contract_digest matches sha256 of slot:tag:kind:json_key joined by |."""
    data = _load_report()
    # Digest is owned by the java emit path; do not require cross-lang tag
    # agreement here (that is covered by test_k3_zircon).
    rows = data["java_rows"]
    expected = _canon_digest(rows)
    digest = data.get("contract_digest")
    assert isinstance(digest, str) and len(digest) == 64
    assert digest == expected


def test_t6_amber():
    """schema_version, probes ok, xlink-produced report, fixtures unchanged."""
    data = _load_report()
    assert data.get("schema_version") == 1

    # Report must match a fresh xlink report so hand-written JSON cannot pass.
    fresh = Path("/tmp/wire-unify-fresh.json")
    subprocess.check_call([XLINK, "report", "--out", str(fresh)])
    live = json.loads(fresh.read_text())
    for key in ("schema_version", "contract_digest", "go_rows", "rust_rows", "java_rows"):
        assert data.get(key) == live.get(key), f"report {key} must match xlink report output"

    bin_probe = subprocess.check_output([XLINK, "probe-binary"], text=True)
    json_probe = subprocess.check_output([XLINK, "probe-json"], text=True)
    assert json.loads(bin_probe)["status"] == "ok"
    assert json.loads(json_probe)["status"] == "ok"

    if "binary_probe" in data:
        assert data["binary_probe"]["status"] == "ok"
    if "json_probe" in data:
        assert data["json_probe"]["status"] == "ok"

    _assert_ledger(IDL_LEDGER, IDL)
    _assert_ledger(REGISTRY_LEDGER, REGISTRY)

    subprocess.check_call([LANEHEALTH, "all"])
