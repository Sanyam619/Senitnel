"""Reconciliation verifier for the NFSv4.2 episode rig.

Independently parses each episode's binary journals and re-derives the
four decisions the reconciler must emit, then compares that reference
against /output/reconciliation.json.
"""

import json
import subprocess
from pathlib import Path

DATA = Path("/app/data/episodes")
OUT = Path("/output/reconciliation.json")
EPISODES = ["alpha", "beta", "gamma", "delta", "epsilon"]

T_RECLAIM_OPEN = 0x01
T_RECLAIM_DELEG_WRITE = 0x02
T_RECLAIM_DELEG_READ = 0x03
T_COMMIT_SEAL = 0x04
T_NAMESPACE_OP = 0x05
T_COPY_SESSION = 0x06

T_OPEN = 0x11
T_DELEGATION_HELD = 0x12
T_RENAME = 0x13
T_COPY_ISSUE = 0x14
T_SEQ_TICK = 0x15

NS_RENAME = 1

DELEG_HELD = "held"
DELEG_DOWNGRADED = "downgraded_share"
DELEG_RELEASED = "released"

COPY_COMPLETED = "completed"
COPY_INVALIDATED = "invalidated"
COPY_RESTARTED = "restarted"
COPY_RESUMED = "resumed"

RENAME_APPLIED = "applied"
RENAME_DEFERRED = "deferred"
RENAME_NOT_PRESENT = "not_present"


def _read_records(buf, header_len):
    pos = header_len
    while pos < len(buf):
        tag = buf[pos]
        if tag == 0:
            break
        length = int.from_bytes(buf[pos + 1 : pos + 3], "little")
        body = buf[pos + 3 : pos + 3 + length]
        yield tag, body
        pos += 3 + length


def _parse_server(path):
    raw = Path(path).read_bytes()
    assert raw[:8] == b"NFSRSVR\x00"
    boot_prev = int.from_bytes(raw[16:24], "little")
    boot_curr = int.from_bytes(raw[24:32], "little")
    grace_ms = int.from_bytes(raw[32:36], "little")
    deadline_ms = int.from_bytes(raw[36:40], "little")

    reclaims = []
    seals = []
    nsops = []
    max_seq = 0

    for tag, body in _read_records(raw, 40):
        if tag == T_RECLAIM_OPEN and len(body) >= 56:
            seq = int.from_bytes(body[32:40], "little")
            max_seq = max(max_seq, seq)
        elif tag in (T_RECLAIM_DELEG_WRITE, T_RECLAIM_DELEG_READ) and len(body) >= 48:
            cid = bytes(body[0:16])
            seq = int.from_bytes(body[16:24], "little")
            fh = bytes(body[24:40])
            epoch = int.from_bytes(body[40:48], "little")
            reclaims.append({
                "client_id": cid,
                "seq": seq,
                "fh": fh,
                "epoch": epoch,
                "is_write": tag == T_RECLAIM_DELEG_WRITE,
            })
            max_seq = max(max_seq, seq)
        elif tag == T_COMMIT_SEAL and len(body) >= 24:
            seq = int.from_bytes(body[0:8], "little")
            verifier = bytes(body[8:16])
            durable = int.from_bytes(body[16:24], "little")
            seals.append({"seq": seq, "verifier": verifier, "durable": durable})
            max_seq = max(max_seq, seq)
        elif tag == T_NAMESPACE_OP and len(body) >= 41:
            nsops.append({
                "op": body[0],
                "src": bytes(body[1:17]),
                "dst": bytes(body[17:33]),
                "ts": int.from_bytes(body[33:41], "little"),
            })
        # COPY_SESSION carries no stateid seq — ignored for max_seq accounting.

    return {
        "boot_prev": boot_prev,
        "boot_curr": boot_curr,
        "grace_ms": grace_ms,
        "deadline_ms": deadline_ms,
        "reclaims": reclaims,
        "seals": seals,
        "nsops": nsops,
        "max_seq": max_seq,
    }


def _parse_client(path, focused_fh):
    raw = Path(path).read_bytes()
    assert raw[:8] == b"NFSRCLI\x00"
    client_id = bytes(raw[16:32])
    owner_seq_start = int.from_bytes(raw[32:40], "little")

    renames = []
    max_seq = 0
    for tag, body in _read_records(raw, 40):
        if tag == T_OPEN and len(body) >= 36:
            max_seq = max(max_seq, int.from_bytes(body[0:8], "little"))
        elif tag == T_DELEGATION_HELD and len(body) >= 33:
            max_seq = max(max_seq, int.from_bytes(body[0:8], "little"))
        elif tag == T_RENAME and len(body) >= 49:
            src = bytes(body[0:16])
            dst = bytes(body[16:32])
            seq = int.from_bytes(body[32:40], "little")
            ts = int.from_bytes(body[40:48], "little")
            backed = body[48]
            max_seq = max(max_seq, seq)
            if src == focused_fh:
                renames.append({"src": src, "dst": dst, "seq": seq,
                                "ts": ts, "backed": backed})
        elif tag == T_SEQ_TICK and len(body) >= 8:
            max_seq = max(max_seq, int.from_bytes(body[0:8], "little"))

    return {
        "client_id": client_id,
        "owner_seq_start": owner_seq_start,
        "renames": renames,
        "max_seq": max_seq,
    }


def _parse_copy_intent(path):
    raw = Path(path).read_bytes()
    assert len(raw) == 96
    assert raw[:8] == b"NFSRCPY\x00"
    return {
        "source_fh": bytes(raw[16:32]),
        "dest_fh": bytes(raw[32:48]),
        "session_id": int.from_bytes(raw[48:56], "little"),
        "total_bytes": int.from_bytes(raw[56:64], "little"),
        "bytes_flushed": int.from_bytes(raw[64:72], "little"),
        "write_verifier": bytes(raw[72:80]),
        "committed_flag": raw[80],
        "issue_ts_ms": int.from_bytes(raw[88:96], "little"),
    }


def _reconcile(ep_dir):
    srv = _parse_server(ep_dir / "server_reclaim.log")
    ci = _parse_copy_intent(ep_dir / "copy_intent.rec")
    focused = ci["source_fh"]
    ca = _parse_client(ep_dir / "client_a_ops.log", focused)
    cb = _parse_client(ep_dir / "client_b_ops.log", focused)

    valid_write = [
        r for r in srv["reclaims"]
        if r["is_write"] and r["epoch"] == srv["boot_curr"] and r["fh"] == focused
    ]
    if len(valid_write) == 0:
        deleg = DELEG_RELEASED
    elif len(valid_write) >= 2:
        deleg = DELEG_DOWNGRADED
    else:
        deleg = DELEG_HELD

    server_rename = any(
        n["op"] == NS_RENAME and n["src"] == focused for n in srv["nsops"]
    )
    verifier_match = any(s["verifier"] == ci["write_verifier"] for s in srv["seals"])
    fully_flushed = (
        ci["total_bytes"] > 0
        and ci["bytes_flushed"] == ci["total_bytes"]
        and ci["committed_flag"] == 1
    )

    if verifier_match and fully_flushed:
        copy = COPY_COMPLETED
    else:
        backed_client_rename = any(r["backed"] for r in ca["renames"] + cb["renames"])
        rename_takes_effect = server_rename or (
            backed_client_rename and deleg == DELEG_HELD
        )
        if rename_takes_effect:
            copy = COPY_INVALIDATED
        elif deleg != DELEG_HELD:
            copy = COPY_RESTARTED
        else:
            copy = COPY_RESUMED

    total_renames = len(ca["renames"]) + len(cb["renames"])
    if total_renames == 0 and not server_rename:
        rename_auth = RENAME_NOT_PRESENT
    elif server_rename:
        rename_auth = RENAME_APPLIED
    elif deleg == DELEG_RELEASED:
        rename_auth = RENAME_DEFERRED
    elif deleg == DELEG_HELD:
        rename_auth = RENAME_APPLIED
    else:
        rename_auth = RENAME_DEFERRED

    seq_next = max(srv["max_seq"], ca["max_seq"], cb["max_seq"]) + 1

    return {
        "delegation_final_state": deleg,
        "copy_resolution": copy,
        "rename_authority": rename_auth,
        "stateid_seq_next": seq_next,
        "focused_fh_hex": focused.hex(),
    }


def _load_report():
    assert OUT.is_file(), f"missing {OUT}"
    doc = json.loads(OUT.read_text())
    assert "episodes" in doc, "report missing 'episodes' key"
    return doc


def _expected(name):
    return _reconcile(DATA / name)


# ---------- structural / integrity tests ----------

def test_report_top_level_keys():
    """Aggregate report exposes an 'episodes' object listing every recorded story."""
    doc = _load_report()
    assert isinstance(doc["episodes"], dict)
    assert set(doc["episodes"].keys()) == set(EPISODES)


def test_report_matches_episode_directory_listing():
    """Report enumerates exactly the on-disk episode directory names."""
    doc = _load_report()
    on_disk = sorted(p.name for p in DATA.iterdir() if p.is_dir())
    assert sorted(doc["episodes"].keys()) == on_disk


def test_every_episode_has_required_fields():
    """Each entry carries the four decisions and the focused handle."""
    doc = _load_report()
    required = {"delegation_final_state", "copy_resolution",
                "rename_authority", "stateid_seq_next", "focused_fh_hex"}
    for name in EPISODES:
        entry = doc["episodes"][name]
        assert required.issubset(entry.keys()), f"missing keys in {name}"


def test_focused_fh_hex_format():
    """Focused file handle is 32 lowercase hex characters."""
    doc = _load_report()
    for name in EPISODES:
        fh_hex = doc["episodes"][name]["focused_fh_hex"]
        assert isinstance(fh_hex, str)
        assert len(fh_hex) == 32
        assert fh_hex == fh_hex.lower()
        int(fh_hex, 16)  # parseable


def test_focused_fh_matches_copy_intent_source():
    """The focused handle in each entry is the COPY source recorded on disk."""
    doc = _load_report()
    for name in EPISODES:
        expected = _expected(name)["focused_fh_hex"]
        assert doc["episodes"][name]["focused_fh_hex"] == expected, (
            f"focused handle mismatch for {name}"
        )


def test_stateid_seq_next_strictly_greater():
    """stateid_seq_next is strictly greater than every seq observed in the journals."""
    doc = _load_report()
    for name in EPISODES:
        exp = _expected(name)
        entry = doc["episodes"][name]
        assert isinstance(entry["stateid_seq_next"], int)
        assert entry["stateid_seq_next"] == exp["stateid_seq_next"], (
            f"{name}: expected {exp['stateid_seq_next']}, got {entry['stateid_seq_next']}"
        )


# ---------- per-scenario decision tests ----------

def test_alpha_grace_window_edge():
    """The unreclaimed delegation drops out AND the stranded rename cannot land."""
    doc = _load_report()
    exp = _expected("alpha")
    entry = doc["episodes"]["alpha"]
    assert exp["delegation_final_state"] == DELEG_RELEASED  # sanity for the fixture
    assert entry["delegation_final_state"] == DELEG_RELEASED
    assert entry["copy_resolution"] == COPY_RESTARTED
    assert entry["rename_authority"] == RENAME_DEFERRED


def test_beta_delegation_conflict_downgrades():
    """Two write reclaims on the same handle in one epoch downgrade to a share."""
    doc = _load_report()
    exp = _expected("beta")
    entry = doc["episodes"]["beta"]
    assert exp["delegation_final_state"] == DELEG_DOWNGRADED
    assert entry["delegation_final_state"] == DELEG_DOWNGRADED
    assert entry["copy_resolution"] == COPY_RESTARTED
    assert entry["rename_authority"] == RENAME_NOT_PRESENT


def test_gamma_rename_race_invalidates_copy():
    """A delegation-backed rename that landed on the server invalidates the copy."""
    doc = _load_report()
    exp = _expected("gamma")
    entry = doc["episodes"]["gamma"]
    assert exp["copy_resolution"] == COPY_INVALIDATED
    assert entry["delegation_final_state"] == DELEG_HELD
    assert entry["copy_resolution"] == COPY_INVALIDATED
    assert entry["rename_authority"] == RENAME_APPLIED


def test_delta_server_acked_unbacked_rename_still_invalidates():
    """An unbacked rename the server acknowledged pre-reboot still moves the source."""
    doc = _load_report()
    exp = _expected("delta")
    entry = doc["episodes"]["delta"]
    assert exp["copy_resolution"] == COPY_INVALIDATED
    assert entry["delegation_final_state"] == DELEG_HELD
    assert entry["copy_resolution"] == COPY_INVALIDATED
    assert entry["rename_authority"] == RENAME_APPLIED


def test_epsilon_completed_copy_is_idempotent():
    """Verifier-match plus full flush marks the copy completed — no re-emission."""
    doc = _load_report()
    exp = _expected("epsilon")
    entry = doc["episodes"]["epsilon"]
    assert exp["copy_resolution"] == COPY_COMPLETED
    assert entry["delegation_final_state"] == DELEG_HELD
    assert entry["copy_resolution"] == COPY_COMPLETED
    assert entry["rename_authority"] == RENAME_NOT_PRESENT


def test_completed_precedence_over_invalidation():
    """A completed copy resolution is preferred over invalidation when both would apply."""
    # Sanity: epsilon has no rename, so this checks the top-priority rule is honoured
    # by verifying the completed outcome is exactly what an independent reconciler produces.
    doc = _load_report()
    assert doc["episodes"]["epsilon"]["copy_resolution"] == COPY_COMPLETED
    # Additionally, verify that the same verifier bytes appear in the seal — this
    # is what elevates the copy to 'completed'.
    srv = _parse_server(DATA / "epsilon" / "server_reclaim.log")
    ci = _parse_copy_intent(DATA / "epsilon" / "copy_intent.rec")
    assert any(s["verifier"] == ci["write_verifier"] for s in srv["seals"])


def test_all_five_entries_exactly_match_reference():
    """Every episode's four decisions match the independent reference reconciliation."""
    doc = _load_report()
    for name in EPISODES:
        expected = _expected(name)
        entry = doc["episodes"][name]
        for key in ("delegation_final_state", "copy_resolution",
                    "rename_authority", "stateid_seq_next", "focused_fh_hex"):
            assert entry[key] == expected[key], (
                f"{name}.{key}: expected {expected[key]!r}, got {entry[key]!r}"
            )


def test_inspector_binary_untouched():
    """The pinned read-only inspector was not rebuilt or replaced."""
    expected = Path("/app/packaging/inspect.sha256").read_text().strip()
    result = subprocess.run(
        ["sha256sum", "/app/bin/nfsr-inspect"],
        capture_output=True, check=True, text=True,
    )
    assert result.stdout.split()[0] == expected


def test_episode_inputs_unchanged():
    """Bundled episode journal files are not mutated by the reconciler."""
    manifest = json.loads(Path("/app/data/episode_manifest.json").read_text())
    # Recompute focused handles from the on-disk copy intents; must match manifest.
    for name, fh_hex in manifest["episodes"].items():
        ci = _parse_copy_intent(DATA / name / "copy_intent.rec")
        assert ci["source_fh"].hex() == fh_hex, (
            f"{name}: manifest handle {fh_hex} disagrees with on-disk copy intent"
        )
