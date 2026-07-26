"""Verifier for fleet crash-export reconciliation with live admin state.

Independently re-derives expected roster/borrow/payload/fragment outcomes
from episode fixtures under /app/data/episodes, then compares against
/output/reconciliation.json. Also asserts drop-in fold, journal cutover,
generation alignment, volume holds, and sealed inode attaches.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

DATA = Path("/app/data/episodes")
OUT = Path("/output")
REPORT = OUT / "reconciliation.json"
RESTORED = OUT / "restored"
STAMP = OUT / "meta" / "run.stamp"
FLEETPEEK = Path("/app/bin/fleetpeek")
FLEETPEEK_PIN = Path("/app/packaging/fleetpeek.sha256")
EPISODES_PIN = Path("/app/packaging/episodes.sha256")
SITE_STD = Path("/etc/fleet/site_standard.conf")
ACTIVE = Path("/etc/fleet/reconcile.conf")
DROPIN = Path("/etc/fleet/reconcile.d")
VOL_ROOT = Path("/var/lib/fleet/volumes")
RT_ROOT = Path("/var/lib/fleet/runtime")
LEASE_DIR = Path("/var/lib/fleet/leases")
GATE_DIR = Path("/var/run/fleet/gate")
STATE = Path("/var/lib/fleet/state")
JOURNAL = Path("/var/lib/fleet/ops/journal.jsonl")
FLEETD_ENV = Path("/etc/fleet/fleetd.env")

EPISODES = ["alpha", "beta", "gamma", "delta", "epsilon"]


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha(path.read_bytes())


def _parse_conf(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _fold_dropins() -> dict[str, str]:
    merged: dict[str, str] = {}
    if not DROPIN.is_dir():
        return merged
    for path in sorted(DROPIN.glob("*.conf")):
        merged.update(_parse_conf(path.read_text()))
    return merged


def _roster(ep: Path) -> list[str]:
    rows = []
    for line in (ep / "coordinator.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    seal_ep = max((r["epoch"] for r in rows if r.get("tag") == "seal"), default=None)
    labs = set()
    for r in rows:
        if r.get("tag") not in ("admit", "reclaim"):
            continue
        if seal_ep is not None and r.get("epoch", 0) > seal_ep:
            continue
        if "lab" in r:
            labs.add(r["lab"])
    return sorted(labs)


def _borrow(ep: Path, pol: dict[str, str]) -> str | None:
    claims = json.loads((ep / "leases.json").read_text())["claims"]
    gates = json.loads((ep / "quarantine.json").read_text())["peers"]
    if pol.get("precedence_mode") == "seal_first" and pol.get("borrow_gate") == "live_and_clear":
        eligible = [
            c for c in claims if c.get("live") and not gates.get(c["peer"], False)
        ]
        if not eligible:
            return None
        sealed = [c for c in eligible if c.get("sealed")]
        pool = sealed if sealed else eligible
        return min(pool, key=lambda c: c["ts"])["peer"]
    live = [c for c in claims if c.get("live")]
    if not live:
        return None
    return max(live, key=lambda c: c["ts"])["peer"]


def _payload(ep_name: str) -> bytes:
    return (VOL_ROOT / ep_name / "sealed" / "payload.bin").read_bytes()


def _fragments(ep: Path, pol: dict[str, str]) -> bytes:
    parts = json.loads((ep / "fragments.json").read_text())["parts"]
    if pol.get("fragment_order") == "seal_ordinal":
        ordered = sorted(parts, key=lambda p: p["seal_ord"])
    else:
        ordered = sorted(parts, key=lambda p: p["offset"])
    return b"".join(bytes.fromhex(p["bytes_hex"]) for p in ordered)


def _decision(name: str, roster: list[str], peer: str | None, pol: dict[str, str]) -> str:
    if name == "alpha":
        return (
            "provisional_kept"
            if ("beacon" in roster or "atlas" in roster)
            else "provisional_dropped"
        )
    if name == "beta":
        return "sealed_lease_wins" if peer == "ridge" else "newer_lease_wins"
    if name == "gamma":
        return "sealed_lineage"
    if name == "delta":
        return (
            "seal_ordinal_weave"
            if pol.get("fragment_order") == "seal_ordinal"
            else "offset_weave"
        )
    if name == "epsilon":
        if (
            peer == "cinder"
            and pol.get("precedence_mode") == "seal_first"
            and pol.get("borrow_gate") == "live_and_clear"
        ):
            return "clear_sealed_borrow"
        return "policy_mismatch_borrow"
    return "unknown"


def _load_episode_pins() -> dict[str, str]:
    assert EPISODES_PIN.is_file(), "missing /app/packaging/episodes.sha256"
    pins: dict[str, str] = {}
    for line in EPISODES_PIN.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        digest, path = line.split(None, 1)
        pins[path] = digest
    assert pins, "episodes.sha256 is empty"
    return pins


def _assert_episode_pins() -> None:
    pins = _load_episode_pins()
    for rel, digest in pins.items():
        path = Path("/app") / rel
        assert path.is_file(), f"missing pinned crash-export input {path}"
        assert _sha_file(path) == digest, f"mutated crash-export input {path}"


def expected_for(name: str) -> dict:
    """Reference view assuming site-standard policy is armed and attaches correct."""
    ep = DATA / name
    pol = _parse_conf(SITE_STD.read_text())
    roster = _roster(ep)
    peer = _borrow(ep, pol)
    payload = _payload(name)
    frag = _fragments(ep, pol)
    return {
        "roster_final": roster,
        "borrow_peer": peer,
        "payload_digest": _sha(payload),
        "fragment_digest": _sha(frag),
        "decision": _decision(name, roster, peer, pol),
    }


def _load_report():
    assert REPORT.is_file(), "missing /output/reconciliation.json"
    return json.loads(REPORT.read_text())


def _sealed_cutover_hold() -> str:
    target = int((STATE / "gen.target").read_text().strip())
    hold = None
    for line in JOURNAL.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("tag") == "cutover" and row.get("mode") == "seal" and int(row.get("gen", -1)) == target:
            hold = row["hold"]
    assert hold is not None, "journal missing sealed cutover for target gen"
    return hold


def _is_sealed_attach(ep: str) -> bool:
    sealed = VOL_ROOT / ep / "sealed" / "payload.bin"
    payload = RT_ROOT / ep / "payload.bin"
    if not payload.is_file() or not sealed.is_file():
        return False
    if os.stat(payload).st_ino != os.stat(sealed).st_ino:
        return False
    decoy = VOL_ROOT / ep / "decoy" / "payload.bin"
    if decoy.is_file() and os.stat(payload).st_ino == os.stat(decoy).st_ino:
        return False
    return _sha_file(payload) == _sha_file(sealed)


def test_all_episodes_present_in_report():
    """Every crash-export episode must appear under episodes."""
    data = _load_report()
    assert "episodes" in data
    for name in EPISODES:
        assert name in data["episodes"], f"missing episode {name}"


def test_report_schema_and_decisions():
    """Per-episode fields must match independently derived expectations."""
    data = _load_report()["episodes"]
    for name in EPISODES:
        exp = expected_for(name)
        row = data[name]
        assert row["roster_final"] == exp["roster_final"]
        assert row["borrow_peer"] == exp["borrow_peer"]
        assert row["payload_digest"] == exp["payload_digest"]
        assert row["fragment_digest"] == exp["fragment_digest"]
        assert row["decision"] == exp["decision"]


def test_restored_trees_match_hashes():
    """Restored payload/fragment bytes must match report digests."""
    data = _load_report()["episodes"]
    for name in EPISODES:
        base = RESTORED / name
        payload = base / "payload.bin"
        frag = base / "fragments.bin"
        report = base / "report.json"
        assert payload.is_file(), f"missing {payload}"
        assert frag.is_file(), f"missing {frag}"
        assert report.is_file(), f"missing {report}"
        assert _sha_file(payload) == data[name]["payload_digest"]
        assert _sha_file(frag) == data[name]["fragment_digest"]
        local = json.loads(report.read_text())
        assert local["roster_final"] == data[name]["roster_final"]
        assert local["borrow_peer"] == data[name]["borrow_peer"]
        assert local["decision"] == data[name]["decision"]


def test_alpha_drops_post_seal_provisional():
    """Alpha must not admit labs only seen in post-seal reclaim/admit rows."""
    row = _load_report()["episodes"]["alpha"]
    exp = expected_for("alpha")
    assert "beacon" not in row["roster_final"]
    assert "atlas" not in row["roster_final"]
    assert row["roster_final"] == exp["roster_final"]
    assert row["decision"] == exp["decision"]


def test_beta_sealed_lease_wins_over_newer():
    """Beta: sealed precedence + earliest sealed ts (not earliest-all / latest-sealed)."""
    row = _load_report()["episodes"]["beta"]
    exp = expected_for("beta")
    export = json.loads((DATA / "beta" / "leases.json").read_text())["claims"]
    by_peer = {c["peer"]: c for c in export}
    assert by_peer["atlas"]["ts"] < by_peer["ridge"]["ts"] < by_peer["mesa"]["ts"]
    assert by_peer["atlas"]["sealed"] is False
    assert by_peer["ridge"]["sealed"] is True
    assert by_peer["mesa"]["sealed"] is True
    assert row["borrow_peer"] == "ridge"
    assert row["borrow_peer"] != "atlas"
    assert row["borrow_peer"] != "mesa"
    assert row["borrow_peer"] == exp["borrow_peer"]
    assert row["decision"] == exp["decision"]
    lease = json.loads((LEASE_DIR / "beta.json").read_text())
    peers = {c["peer"] for c in lease["claims"]}
    assert "ridge" in peers
    assert len(lease["claims"]) >= 2


def test_gamma_uses_sealed_shelf_not_decoy():
    """Gamma payload must be sealed volume bytes via runtime attach, not decoy."""
    row = _load_report()["episodes"]["gamma"]
    sealed = VOL_ROOT / "gamma" / "sealed" / "payload.bin"
    decoy = VOL_ROOT / "gamma" / "decoy" / "payload.bin"
    assert sealed.is_file() and decoy.is_file()
    assert row["payload_digest"] == _sha_file(sealed)
    assert row["payload_digest"] != _sha_file(decoy)
    restored = RESTORED / "gamma" / "payload.bin"
    assert restored.read_bytes() == sealed.read_bytes()
    assert _is_sealed_attach("gamma")


def test_delta_fragment_seal_ordinal_not_offset():
    """Delta fragment weave follows seal_ord, which reverses offset order."""
    row = _load_report()["episodes"]["delta"]
    parts = json.loads((DATA / "delta" / "fragments.json").read_text())["parts"]
    by_ord = sorted(parts, key=lambda p: p["seal_ord"])
    by_off = sorted(parts, key=lambda p: p["offset"])
    correct = b"".join(bytes.fromhex(p["bytes_hex"]) for p in by_ord)
    wrong = b"".join(bytes.fromhex(p["bytes_hex"]) for p in by_off)
    assert correct != wrong
    assert row["fragment_digest"] == _sha(correct)
    assert row["fragment_digest"] != _sha(wrong)
    assert row["decision"] == expected_for("delta")["decision"]


def test_epsilon_policy_and_quarantine_borrow():
    """Epsilon picks the sealed clear peer under exact site-standard tokens."""
    row = _load_report()["episodes"]["epsilon"]
    exp = expected_for("epsilon")
    assert row["borrow_peer"] == exp["borrow_peer"]
    assert row["decision"] == exp["decision"]
    std = _parse_conf(SITE_STD.read_text())
    active = _parse_conf(ACTIVE.read_text())
    for key in ("precedence_mode", "borrow_gate", "fragment_order"):
        assert active[key] == std[key], f"active policy synonym/mismatch on {key}"
    assert (GATE_DIR / "epsilon" / "ridge").is_file(), "epsilon/ridge must be gated"
    assert not (GATE_DIR / "epsilon" / "cinder").is_file(), "epsilon/cinder must not be gated"
    assert not (GATE_DIR / "beta" / "ridge").is_file(), "beta/ridge must not be gated"


def test_toolchain_stamp_records_armed_policy():
    """run.stamp must reflect exact site-standard tokens from a real run."""
    assert STAMP.is_file()
    body = STAMP.read_text().strip()
    std = _parse_conf(SITE_STD.read_text())
    assert std["precedence_mode"] in body
    assert std["borrow_gate"] in body
    assert std["fragment_order"] in body
    for tok in ("prefer_seal", "live_or_clear", "byte_offset"):
        if tok not in std.values():
            assert tok not in body


def test_admin_volume_attach_and_policy():
    """Each episode runtime payload must attach sealed volume; policy exact."""
    std = _parse_conf(SITE_STD.read_text())
    active = _parse_conf(ACTIVE.read_text())
    for key in ("precedence_mode", "borrow_gate", "fragment_order"):
        assert active[key] == std[key]
    for name in EPISODES:
        assert _is_sealed_attach(name), f"runtime payload not sealed attach for {name}"
        assert (LEASE_DIR / f"{name}.json").is_file(), f"missing lease for {name}"
    assert Path("/var/run/fleet/fleetd.pid").is_file()


def test_dropin_fold_matches_site_standard():
    """Fold matches site standard; live 90-local.conf must remain present."""
    local_path = DROPIN / "90-local.conf"
    assert local_path.is_file(), "live 90-local.conf must remain present (not deleted)"
    local = _parse_conf(local_path.read_text())
    folded = _fold_dropins()
    active = _parse_conf(ACTIVE.read_text())
    std = _parse_conf(SITE_STD.read_text())
    for key in ("precedence_mode", "borrow_gate", "fragment_order"):
        assert local.get(key) == std[key], f"90-local.conf mismatch on {key}"
        assert folded.get(key) == std[key], f"drop-in fold mismatch on {key}"
        assert active.get(key) == folded.get(key), f"effective != fold on {key}"
    assert "prefer_seal" not in folded.values()
    assert "live_or_clear" not in folded.values()
    assert "byte_offset" not in folded.values()
    # Abort package may still hold synonyms; live drop-in must not.
    abort = Path("/var/lib/fleet/ops/abort.d/90-local.conf")
    assert abort.is_file(), "abort.d residue must remain present"
    abort_cfg = _parse_conf(abort.read_text())
    assert abort_cfg.get("precedence_mode") == "prefer_seal"
    assert local.get("precedence_mode") != abort_cfg.get("precedence_mode")


def test_generation_aligned_to_sealed_cutover():
    """gen.live must equal gen.target after sealed cutover apply."""
    target = (STATE / "gen.target").read_text().strip()
    live = (STATE / "gen.live").read_text().strip()
    assert target == "7"
    assert live == target
    assert (STATE / "attach.intent").read_text().strip() == "seal"
    assert (STATE / "hold.token").read_text().strip() == _sealed_cutover_hold()


def test_cutover_receipt_suppresses_abort_residue():
    """cutover.ok is key=value; skips abort rematerialize; abort.d keeps synonyms."""
    hold = _sealed_cutover_hold()
    receipt = STATE / "cutover.ok"
    assert receipt.is_file(), "missing /var/lib/fleet/state/cutover.ok"
    raw = receipt.read_text()
    assert "{" not in raw and "[" not in raw, "cutover.ok must be key=value text, not JSON"
    body = _parse_conf(raw)
    assert body.get("gen") == "7"
    assert body.get("hold") == hold
    assert body.get("mode") == "seal"
    local_path = DROPIN / "90-local.conf"
    assert local_path.is_file(), "suppressing abort rematerialize must not delete 90-local.conf"
    local = _parse_conf(local_path.read_text())
    std = _parse_conf(SITE_STD.read_text())
    for key in ("precedence_mode", "borrow_gate", "fragment_order"):
        assert local.get(key) == std[key], f"live 90-local must be rewritten to site-standard on {key}"
    assert local.get("precedence_mode") != "prefer_seal"
    # Abort package is forensic residue: remain present with abort synonyms.
    abort = Path("/var/lib/fleet/ops/abort.d/90-local.conf")
    assert abort.is_file(), "abort.d residue must remain present"
    abort_cfg = _parse_conf(abort.read_text())
    assert abort_cfg.get("precedence_mode") == "prefer_seal"
    assert abort_cfg.get("borrow_gate") == "live_or_clear"
    assert abort_cfg.get("fragment_order") == "byte_offset"


def test_runtime_holds_match_sealed_cutover():
    """Holds + lineage: attach.intent=seal, PAYLOAD_LINEAGE=sealed (volume dir)."""
    hold = _sealed_cutover_hold()
    env = _parse_conf(FLEETD_ENV.read_text())
    assert env.get("HOLD_TOKEN") == hold
    assert env.get("PAYLOAD_LINEAGE") == "sealed"
    assert (STATE / "attach.intent").read_text().strip() == "seal"
    assert env.get("PAYLOAD_LINEAGE") != (STATE / "attach.intent").read_text().strip()
    for name in EPISODES:
        hold_path = RT_ROOT / name / ".hold"
        assert hold_path.is_file(), f"missing hold for {name}"
        assert hold_path.read_text().strip() == hold
        assert _is_sealed_attach(name), f"lineage misarm undid sealed attach for {name}"


def test_live_leases_preserve_export_claim_sets():
    """Live lease bags must keep full export claim sets (not atlas-only stubs)."""
    for name in ("beta", "epsilon"):
        export = json.loads((DATA / name / "leases.json").read_text())
        live = json.loads((LEASE_DIR / f"{name}.json").read_text())
        export_peers = {c["peer"] for c in export["claims"]}
        live_peers = {c["peer"] for c in live["claims"]}
        assert export_peers == live_peers
        assert "atlas" in live_peers
        assert len(live["claims"]) >= 2


def test_fleetpeek_digest_unmodified():
    """Pinned read-only inspector binary must keep its packaging digest."""
    assert FLEETPEEK.is_file()
    assert FLEETPEEK_PIN.is_file()
    pinned = FLEETPEEK_PIN.read_text().strip().split()[0]
    assert _sha_file(FLEETPEEK) == pinned


def test_episode_inputs_immutable():
    """Crash-export inputs must stay byte-identical to packaging pins."""
    _assert_episode_pins()
    for name in EPISODES:
        seal = DATA / name / "volume_seal.json"
        assert seal.is_file()
        obj = json.loads(seal.read_text())
        assert obj["shelf_key"] == "sealed"
        assert (DATA / name / "coordinator.jsonl").is_file()
        assert (DATA / name / "leases.json").is_file()


def test_reject_unmodified_broken_baseline_markers():
    """Broken baseline markers must not survive a correct recovery."""
    data = _load_report()["episodes"]
    assert "beacon" not in data["alpha"]["roster_final"]
    assert data["beta"]["borrow_peer"] != "atlas"
    assert data["beta"]["borrow_peer"] != "mesa"
    decoy_hash = _sha_file(VOL_ROOT / "gamma" / "decoy" / "payload.bin")
    assert data["gamma"]["payload_digest"] != decoy_hash
    parts = json.loads((DATA / "delta" / "fragments.json").read_text())["parts"]
    wrong = b"".join(
        bytes.fromhex(p["bytes_hex"]) for p in sorted(parts, key=lambda x: x["offset"])
    )
    assert data["delta"]["fragment_digest"] != _sha(wrong)
    assert data["epsilon"]["borrow_peer"] != "atlas"
    assert data["epsilon"]["borrow_peer"] != "ridge"
    active = _parse_conf(ACTIVE.read_text())
    assert active.get("precedence_mode") != "prefer_seal"
    assert _is_sealed_attach("gamma")
    assert (STATE / "gen.live").read_text().strip() != "3"
    assert (STATE / "hold.token").read_text().strip() != "lab-tmp"
    assert (RT_ROOT / "gamma" / ".hold").read_text().strip() != "lab-tmp"
    assert (STATE / "cutover.ok").is_file()
    assert (DROPIN / "90-local.conf").is_file()
    env = _parse_conf(FLEETD_ENV.read_text())
    assert env.get("PAYLOAD_LINEAGE") != "seal"
    assert env.get("PAYLOAD_LINEAGE") != "decoy"
