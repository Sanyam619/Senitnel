"""Outcome tests for PKCS#11 multi-slot authority cutover."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

LEDGER = Path("/output/session-rebind.json")
TOKEN = Path("/data/token")
SEED = Path("/data/fixtures/token-seed")
POLICY = Path("/opt/pk11/config/pin_policy.toml")
PK11 = Path("/opt/pk11")
BIN = PK11 / "bin"
GATE = PK11 / "lib" / "gate.jar"
OPS = PK11 / "lib" / "ops.jar"
OPS_FINGERPRINT = PK11 / "lib" / "ops.sha256"
SCENARIOS = PK11 / "scenarios"
RUNTIME_CP = f"{OPS}:{GATE}:{PK11 / 'classes'}"


def _ensure_helper_wrappers() -> None:
    """Rebind helper scripts to the sealed classpath (bin wrappers are writable)."""
    BIN.mkdir(parents=True, exist_ok=True)
    for tool in ("wireapply", "holdrun", "emitout", "authcheck", "sealgen", "findscan", "slotprobe"):
        path = BIN / tool
        path.write_text(
            "#!/bin/sh\n"
            f'exec java -cp "{RUNTIME_CP}" {tool}.Main "$@"\n',
            encoding="utf-8",
        )
        path.chmod(0o755)


def _assert_ops_sealed() -> None:
    assert GATE.is_file(), "sealed gate missing"
    assert OPS.is_file(), "sealed ops missing"
    assert OPS_FINGERPRINT.is_file(), "ops fingerprint missing"
    expect_raw = OPS_FINGERPRINT.read_text(encoding="utf-8").strip()
    assert expect_raw, "ops fingerprint empty"
    expect = expect_raw.split()[0]
    dig = subprocess.run(
        ["sha256sum", str(OPS)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert dig.returncode == 0, dig.stderr
    got = dig.stdout.strip().split()[0]
    assert got == expect, "ops.jar fingerprint drift (engines must stay sealed)"


def _load() -> dict:
    import json

    assert LEDGER.exists(), f"missing {LEDGER}"
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def _policy_ttl() -> int:
    for line in POLICY.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("ttl_sec"):
            return int(line.split("=", 1)[1].strip())
    raise AssertionError("ttl_sec missing from pin_policy.toml")


def _revoked_epochs() -> set[int]:
    out: set[int] = set()
    journal = TOKEN / "restore.journal"
    if not journal.exists():
        return out
    for line in journal.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(":", 1)
        if len(parts) != 2 or parts[0].strip() != "01":
            continue
        try:
            out.add(int(parts[1].strip(), 16))
        except ValueError:
            pass
    return out


def _live_slot_id() -> int:
    rvk = _revoked_epochs()
    candidates: list[tuple[int, int]] = []
    for line in TOKEN.joinpath("inventory.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "live":
            epoch = int(parts[2]) if len(parts) >= 3 else 0
            if epoch not in rvk:
                candidates.append((int(parts[0]), epoch))
    assert candidates, "no eligible live slot in inventory"
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]


def _effective_ttl() -> int:
    base = _policy_ttl()
    live_id = _live_slot_id()
    override = POLICY.parent / "slot_overrides" / f"{live_id}.toml"
    if override.exists():
        for line in override.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("ttl_sec"):
                val = int(line.split("=", 1)[1].strip())
                if 0 < val < base:
                    return val
    return base


def _required_labels() -> list[str]:
    labels: list[str] = []
    for line in TOKEN.joinpath("labels.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        labels.append(line)
    return labels


def _as_int(value) -> int:
    return int(value)


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _snapshot_token() -> dict[str, str | None]:
    names = [
        "provider.txt",
        "sessions.txt",
        "session.seal",
        "wire.nonce",
        "lattice.tag",
        "reload.marker",
        "inventory.txt",
        "restore.journal",
    ]
    out: dict[str, str | None] = {}
    for name in names:
        path = TOKEN / name
        out[name] = path.read_text(encoding="utf-8") if path.exists() else None
    out["__ledger__"] = LEDGER.read_text(encoding="utf-8") if LEDGER.exists() else None
    return out


def _restore_token(snap: dict[str, str | None]) -> None:
    for name, body in snap.items():
        if name == "__ledger__":
            continue
        path = TOKEN / name
        if body is None:
            path.unlink(missing_ok=True)
        else:
            path.write_text(body, encoding="utf-8")
    ledger_body = snap.get("__ledger__")
    if ledger_body is None:
        LEDGER.unlink(missing_ok=True)
    else:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        LEDGER.write_text(ledger_body, encoding="utf-8")


def _run_cutover() -> None:
    _ensure_helper_wrappers()
    _assert_ops_sealed()
    TOKEN.joinpath("reload.marker").write_text("1\n", encoding="utf-8")
    for tool in ("wireapply", "holdrun", "emitout"):
        result = subprocess.run(
            [str(BIN / tool)],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"{tool} failed: {result.stdout}{result.stderr}"


def _assert_lane_admitted(live_id: int, ttl_limit: int) -> None:
    bound = TOKEN.joinpath("provider.txt").read_text(encoding="utf-8").strip()
    assert bound == f"bound={live_id}", f"provider {bound} != {live_id}"
    assert TOKEN.joinpath("wire.nonce").exists()
    assert TOKEN.joinpath("lattice.tag").exists()
    assert TOKEN.joinpath("session.seal").exists()
    sess = TOKEN.joinpath("sessions.txt").read_text(encoding="utf-8")
    live_rows = [
        ln
        for ln in sess.splitlines()
        if ln.strip() and not ln.startswith("#") and ln.split()[0] == str(live_id)
    ]
    assert live_rows, "missing live session row"
    parts = live_rows[0].split()
    assert parts[1] in {"1", "true"}
    assert 0 < int(parts[2]) <= ttl_limit
    payload = _load()
    for row in payload["slots"]:
        expect = _as_int(row["id"]) == live_id
        assert _as_bool(row.get("provider_bound")) == expect
    for row in payload["certs"]:
        if row.get("label") in set(_required_labels()):
            expect = _as_int(row.get("slot_id")) == live_id
            assert _as_bool(row.get("handle_auth")) == expect
        assert _as_int(row.get("slot_id")) != 29
    auth = subprocess.run(
        [str(BIN / "authcheck")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert auth.returncode == 0, auth.stdout + auth.stderr
    find = subprocess.run(
        [str(BIN / "findscan")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert find.returncode == 0, find.stdout + find.stderr


def test_w4_cobal():
    """Provider bind lands only on the inventory current-lane id."""
    payload = _load()
    live_id = _live_slot_id()
    rows = payload["slots"]
    for row in rows:
        expect_bound = _as_int(row["id"]) == live_id
        if _as_bool(row.get("provider_bound")) != expect_bound:
            raise AssertionError(f"provider_bound mismatch for id={row['id']}")
    bound_line = TOKEN.joinpath("provider.txt").read_text(encoding="utf-8").strip()
    if bound_line != f"bound={live_id}":
        raise AssertionError(f"provider.txt {bound_line}")


def test_n7_quartz():
    """Runtime authorizer accepts only when provider matches the current lane."""
    _ensure_helper_wrappers()
    _assert_ops_sealed()
    live_id = _live_slot_id()
    bound_line = TOKEN.joinpath("provider.txt").read_text(encoding="utf-8").strip()
    assert bound_line == f"bound={live_id}"
    result = subprocess.run(
        [str(BIN / "authcheck")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "accept" in result.stdout.lower()


def test_h2_jade():
    """Current-lane sessions report pin_alive after reload refresh."""
    payload = _load()
    live_id = _live_slot_id()
    matched = [s for s in payload["sessions"] if _as_int(s.get("slot_id")) == live_id]
    assert matched, "missing current-lane session row"
    for row in matched:
        if not _as_bool(row.get("pin_alive")):
            raise AssertionError("pin_alive mismatch on current-lane session")


def test_v9_felsic():
    """Current-lane ttl_sec stays within the effective ceiling after reload."""
    payload = _load()
    live_id = _live_slot_id()
    limit = _effective_ttl()
    matched = [s for s in payload["sessions"] if _as_int(s.get("slot_id")) == live_id]
    assert matched
    for row in matched:
        ttl = _as_int(row["ttl_sec"])
        if not (0 < ttl <= limit):
            raise AssertionError(f"ttl_sec {ttl} outside posted window {limit}")


def test_s5_basalt():
    """Required cert labels get handle_auth on the current-lane id only."""
    payload = _load()
    live_id = _live_slot_id()
    want = set(_required_labels())
    seen_live = set()
    for row in payload["certs"]:
        label = row.get("label")
        if label not in want:
            continue
        expect = _as_int(row.get("slot_id")) == live_id
        if _as_bool(row.get("handle_auth")) != expect:
            raise AssertionError(f"handle_auth mismatch for {label} slot={row.get('slot_id')}")
        if expect:
            seen_live.add(label)
    assert seen_live == want


def test_k8_pyrite():
    """Object-count scan stays green while non-current-lane cert rows stay unauthorized."""
    find = subprocess.run(
        [str(BIN / "findscan")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert find.returncode == 0, find.stdout + find.stderr
    payload = _load()
    live_id = _live_slot_id()
    want = set(_required_labels())
    off_lane = [
        c
        for c in payload["certs"]
        if c.get("label") in want and _as_int(c.get("slot_id")) != live_id
    ]
    assert off_lane, "expected duplicate off-lane cert rows from restore"
    for row in off_lane:
        if _as_bool(row.get("handle_auth")):
            raise AssertionError(f"off-lane handle_auth still set for {row}")


def test_g3_obsidian():
    """Helpers recover after bad bind; prefs generalize across alternate ledgers."""
    seal_path = TOKEN / "session.seal"
    assert seal_path.exists(), "session.seal missing"
    assert seal_path.read_text(encoding="utf-8").strip()
    assert TOKEN.joinpath("wire.nonce").exists()
    assert TOKEN.joinpath("lattice.tag").exists()

    live_id = _live_slot_id()
    limit = _effective_ttl()
    snap = _snapshot_token()
    try:
        TOKEN.joinpath("provider.txt").write_text("bound=23\n", encoding="utf-8")
        TOKEN.joinpath("wire.nonce").unlink(missing_ok=True)
        _run_cutover()
        _assert_lane_admitted(live_id, limit)

        # Alternate restore ledgers must select different authoritative lanes
        # under the same preference lattice (hardcoded single-slot patches fail).
        for name, expect_live, ttl_cap in (
            ("beta", 11, 300),
            ("gamma", 31, 300),
        ):
            inv = SCENARIOS / name / "inventory.txt"
            jrnl = SCENARIOS / name / "restore.journal"
            assert inv.is_file() and jrnl.is_file()
            shutil.copyfile(inv, TOKEN / "inventory.txt")
            shutil.copyfile(jrnl, TOKEN / "restore.journal")
            TOKEN.joinpath("provider.txt").write_text("bound=23\n", encoding="utf-8")
            for stale in ("wire.nonce", "lattice.tag", "session.seal"):
                TOKEN.joinpath(stale).unlink(missing_ok=True)
            # Reset sessions to stretched defaults so holdrun must refresh.
            TOKEN.joinpath("sessions.txt").write_text(
                "# slot pin_alive ttl\n"
                "11 1 86400\n"
                "17 0 86400\n"
                "23 1 86400\n"
                "29 0 1200\n"
                "31 0 86400\n",
                encoding="utf-8",
            )
            _run_cutover()
            _assert_lane_admitted(expect_live, ttl_cap)
    finally:
        _restore_token(snap)


def test_m1_rhyolite():
    """Ledger schema version 1 with required arrays; token-seed marker intact."""
    payload = _load()
    assert payload.get("version") == 1
    assert isinstance(payload.get("slots"), list) and payload["slots"]
    assert isinstance(payload.get("sessions"), list) and payload["sessions"]
    assert isinstance(payload.get("certs"), list) and payload["certs"]
    slot_keys = {"id", "role", "provider_bound"}
    sess_keys = {"slot_id", "pin_alive", "ttl_sec"}
    cert_keys = {"label", "slot_id", "handle_auth"}
    for row in payload["slots"]:
        if not slot_keys <= set(row):
            raise AssertionError("slots row missing required keys")
    for row in payload["sessions"]:
        if not sess_keys <= set(row):
            raise AssertionError("sessions row missing required keys")
    for row in payload["certs"]:
        if not cert_keys <= set(row):
            raise AssertionError("certs row missing required keys")
    assert SEED.joinpath("marker.txt").read_text(encoding="utf-8").strip() == "seed-ok"
    assert SEED.joinpath("restore.journal").exists()
    auth = subprocess.run(
        [str(BIN / "authcheck")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert auth.returncode == 0, auth.stdout + auth.stderr
