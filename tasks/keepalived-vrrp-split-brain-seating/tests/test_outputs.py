"""Verifier for Keepalived VRRP split-brain seating."""

from __future__ import annotations

import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path

REPORT = Path("/output/vrrp-seat.json")
PEER_D = Path("/app/data/vrrp")
EXTRA_D = Path("/var/lib/keepalived/ops/extra")
PIN = Path("/app/packaging/vrrp.sha256")
POLICY_SHEET = Path("/app/config/site_policy.conf")
ETC = Path("/etc/keepalived")
OPS = Path("/var/lib/keepalived/ops")
ABORT = OPS / "abort.d" / "90-local.conf"
LIVE_DROP = Path("/etc/keepalived/conf.d/90-local.conf")
ADVERT = ETC / "runtime" / "advert.map"
RECEIPT = OPS / "state" / "cutover.ok"
GEN_TARGET = OPS / "state" / "generation.target"
GEN_LIVE = OPS / "state" / "generation.live"
CLOCK = OPS / "state" / "clock.epoch"
PREFER = OPS / "prefer.jsonl"
TRANS = OPS / "transitions.jsonl"
TRACK = OPS / "track"
NETIF = OPS / "netif"
LIVE = OPS / "live"
VRRPSEAT = Path("/app/publisher/vrrpseat")


def _run(cmd: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def _reseat() -> dict:
    REPORT.unlink(missing_ok=True)
    proc = _run(["/bin/bash", "/app/ops/run_vrrp_seat.sh"], check=False)
    assert proc.returncode == 0, f"seat failed: {proc.stderr}\n{proc.stdout}"
    assert REPORT.is_file(), "missing /output/vrrp-seat.json"
    return json.loads(REPORT.read_text())


def _parse_kv(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _load_peers() -> dict[str, dict[str, str]]:
    peers: dict[str, dict[str, str]] = {}
    roots = [PEER_D]
    if EXTRA_D.is_dir():
        roots.append(EXTRA_D)
    for root in roots:
        for f in sorted(root.glob("*.conf")):
            kv = _parse_kv(f.read_text())
            if "id" in kv:
                peers[kv["id"]] = kv
    return peers


def _fold_prio() -> dict[str, int]:
    z: dict[str, int] = {}
    conf_d = ETC / "conf.d"
    for f in sorted(conf_d.glob("*.conf")):
        for line in f.read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            op = "set"
            if line.startswith("replace "):
                line = line[len("replace ") :]
                op = "set"
            elif line.startswith("delta "):
                line = line[len("delta ") :]
                op = "delta"
            if "=" not in line:
                continue
            raw, v_s = line.split("=", 1)
            raw, v_s = raw.strip(), v_s.strip()
            if not raw.endswith(".prio"):
                continue
            k = raw.removesuffix(".prio")
            v = int(v_s)
            if op == "delta":
                z[k] = z.get(k, 0) + v
            else:
                z[k] = v
    if TRACK.is_dir():
        for wt in sorted(TRACK.glob("*.wt")):
            name = wt.stem
            status_f = TRACK / f"{name}.status"
            status = status_f.read_text().strip() if status_f.exists() else "DOWN"
            if status != "UP":
                continue
            delta = int(_parse_kv(wt.read_text()).get("delta", "0"))
            z[name] = z.get(name, 0) + delta
    return z


def _pick_batch() -> dict:
    batches = []
    for line in PREFER.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("kind") != "batch":
            continue
        if row.get("sealed") is True and row.get("complete") is True:
            batches.append(row)
    assert batches, "no sealed complete preference batch"
    batches.sort(key=lambda r: int(r.get("gen", -1)))
    return batches[-1]


def _active_moves() -> list[dict]:
    active: dict[str, dict] = {}
    for line in TRANS.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("kind") == "move":
            active[row["eid"]] = row
        elif row.get("kind") == "retract":
            active.pop(row.get("eid"), None)
    return sorted(
        active.values(), key=lambda r: (int(r["vrid"]), int(r["epoch"]), r["eid"])
    )


def _finite_int(v: object) -> bool:
    return isinstance(v, int) and float("-inf") < float(v) < float("inf")


def _expected_doc() -> dict:
    peers = _load_peers()
    prio = _fold_prio()
    batch = _pick_batch()
    tips = {r["id"]: int(r["tip"]) for r in batch["rows"]}
    ranks = {r["id"]: int(r["rank"]) for r in batch["rows"]}
    clock = int(CLOCK.read_text().strip())
    floors = {
        name: int((OPS / "floors" / f"{name}.floor").read_text().strip())
        for name in peers
        if (OPS / "floors" / f"{name}.floor").exists()
    }
    holds: dict[str, int] = {}
    for name in peers:
        hf = OPS / "holds" / f"{name}.hold"
        if hf.exists():
            holds[name] = int(_parse_kv(hf.read_text()).get("until", "0"))
    netifs: dict[str, int] = {}
    for name in peers:
        nf = NETIF / f"{name}.gen"
        if nf.exists():
            netifs[name] = int(nf.read_text().strip())

    elig: dict[str, bool] = {}
    for name in peers:
        held = holds.get(name, 0) > clock
        floor = floors.get(name, 0)
        tip = tips.get(name, 0)
        netif = netifs.get(name, 0)
        elig[name] = (not held) and tip >= floor and netif >= floor

    moves = _active_moves()
    veto = {int(m["vrid"]) for m in moves if m.get("from") == "MASTER"}

    by_vrid: dict[int, list[str]] = {}
    for name, meta in peers.items():
        by_vrid.setdefault(int(meta["vrid"]), []).append(name)

    winners: dict[int, str] = {}
    for vrid, names in by_vrid.items():
        if vrid in veto:
            continue
        best = None
        best_key = None
        for name in names:
            if not elig.get(name, False):
                continue
            key = (int(prio.get(name, int(peers[name].get("base", 0)))), ranks.get(name, 0))
            if best is None or key > best_key:
                best = name
                best_key = key
        if best is not None:
            winners[vrid] = best

    instances = []
    for name in sorted(peers):
        meta = peers[name]
        vrid = int(meta["vrid"])
        state = "MASTER" if winners.get(vrid) == name else "BACKUP"
        instances.append(
            {
                "name": name,
                "vrid": vrid,
                "state": state,
                "priority": int(prio.get(name, int(meta.get("base", 0)))),
                "vip": meta["vip"],
                "generation": tips.get(name, 0),
            }
        )

    transitions = [
        {
            "vrid": int(m["vrid"]),
            "epoch": int(m["epoch"]),
            "from": m["from"],
            "to": m["to"],
        }
        for m in moves
    ]

    masters = [i for i in instances if i["state"] == "MASTER"]
    counts = Counter(i["vrid"] for i in masters)
    seat_ok = True
    if any(c != 1 for c in counts.values()):
        seat_ok = False
    for i in masters:
        if winners.get(i["vrid"]) != i["name"]:
            seat_ok = False
    for vrid, names in by_vrid.items():
        if vrid in veto:
            if any(i["vrid"] == vrid and i["state"] == "MASTER" for i in instances):
                seat_ok = False
            continue
        if vrid in winners and not any(
            i["name"] == winners[vrid] and i["state"] == "MASTER" for i in instances
        ):
            seat_ok = False

    return {
        "schema_tag": "vrrp-seat-v1",
        "instances": instances,
        "transitions": transitions,
        "seat_ok": seat_ok,
    }


def _snapshot_paths(paths: list[Path]) -> dict[str, bytes | None]:
    snap: dict[str, bytes | None] = {}
    for p in paths:
        snap[str(p)] = p.read_bytes() if p.exists() else None
    return snap


def _restore_paths(snap: dict[str, bytes | None]) -> None:
    for path_s, data in snap.items():
        p = Path(path_s)
        if data is None:
            if p.exists():
                if p.is_dir():
                    shutil.rmtree(p)
                else:
                    p.unlink()
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)


def _file_sha256(path: Path) -> str:
    proc = _run(["sha256sum", str(path)], check=False)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.split()[0]


def _assert_advert(doc: dict) -> None:
    assert ADVERT.is_file()
    expected = {
        i["vip"]: i["name"] for i in doc["instances"] if i["state"] == "MASTER"
    }
    got = _parse_kv(ADVERT.read_text())
    assert got == expected


def test_q3_topaz() -> None:
    """Baseline ledger, schema types, advert map, and no duplicate MASTER per VRID."""
    doc = _reseat()
    exp = _expected_doc()
    assert doc["schema_tag"] == "vrrp-seat-v1"
    assert isinstance(doc["instances"], list)
    assert isinstance(doc["transitions"], list)
    assert isinstance(doc["seat_ok"], bool)
    assert doc["seat_ok"] is True
    needed = {"name", "vrid", "state", "priority", "vip", "generation"}
    for row in doc["instances"]:
        assert needed <= set(row)
        assert isinstance(row["name"], str)
        assert _finite_int(row["vrid"])
        assert isinstance(row["state"], str)
        assert _finite_int(row["priority"])
        assert isinstance(row["vip"], str)
        assert _finite_int(row["generation"])
    masters = [i for i in doc["instances"] if i["state"] == "MASTER"]
    counts = Counter(i["vrid"] for i in masters)
    assert all(c == 1 for c in counts.values())
    assert doc["instances"] == exp["instances"]
    assert doc["transitions"] == exp["transitions"]
    _assert_advert(doc)


def test_n4_beryl() -> None:
    """Two seating runs leave byte-identical output and stable live/durable gens."""
    _reseat()
    first = REPORT.read_bytes()
    live1 = GEN_LIVE.read_text()
    _reseat()
    second = REPORT.read_bytes()
    live2 = GEN_LIVE.read_text()
    assert first == second
    assert first.endswith(b"\n")
    assert live1 == live2
    assert live1.strip() == "7"


def test_w7_quartz() -> None:
    """Frozen fixtures and prebuilt publisher stay pinned; novel extra peer seats."""
    assert PIN.is_file()
    peer_digests: dict[str, str] = {}
    seat_digest = None
    for line in PIN.read_text().splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        digest, path = line.split(None, 1)
        path = path.strip()
        if path.endswith("vrrpseat"):
            seat_digest = digest
        else:
            peer_digests[Path(path).name] = digest
    assert seat_digest is not None
    assert seat_digest == _file_sha256(VRRPSEAT)
    assert peer_digests
    for name, digest in peer_digests.items():
        assert _file_sha256(PEER_D / name) == digest

    paths = [
        PREFER,
        ETC / "conf.d" / "70-extra.conf",
        EXTRA_D / "peer_g.conf",
        OPS / "floors" / "peer_g.floor",
        NETIF / "peer_g.gen",
        REPORT,
    ]
    snap = _snapshot_paths(paths)
    try:
        EXTRA_D.mkdir(parents=True, exist_ok=True)
        (EXTRA_D / "peer_g.conf").write_text(
            "id=peer_g\nvrid=53\nvip=10.10.53.1\nbase=80\n"
        )
        (OPS / "floors" / "peer_g.floor").write_text("1\n")
        (NETIF / "peer_g.gen").write_text("7\n")
        (ETC / "conf.d" / "70-extra.conf").write_text("peer_g.prio=140\n")
        batch = _pick_batch()
        rows = list(batch["rows"]) + [{"id": "peer_g", "tip": 7, "rank": 0}]
        new_batch = {
            "kind": "batch",
            "id": "b7x",
            "gen": int(batch["gen"]),
            "sealed": True,
            "complete": True,
            "rows": rows,
        }
        lines = []
        for line in PREFER.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if (
                row.get("kind") == "batch"
                and int(row.get("gen", -1)) == int(batch["gen"])
                and row.get("sealed") is True
                and row.get("complete") is True
            ):
                continue
            lines.append(line)
        lines.append(json.dumps(new_batch, separators=(",", ":")))
        PREFER.write_text("\n".join(lines) + "\n")
        doc = _reseat()
        by_name = {r["name"]: r for r in doc["instances"]}
        assert "peer_g" in by_name
        assert by_name["peer_g"]["state"] == "MASTER"
        assert by_name["peer_g"]["vrid"] == 53
        assert by_name["peer_g"]["priority"] == 140
        _assert_advert(doc)
        for name, digest in peer_digests.items():
            assert _file_sha256(PEER_D / name) == digest
        assert _file_sha256(VRRPSEAT) == seat_digest
    finally:
        _restore_paths(snap)
        if EXTRA_D.exists():
            shutil.rmtree(EXTRA_D)
        _reseat()


def test_v5_coral() -> None:
    """Latest complete sealed preference wins over incomplete later batch."""
    doc = _reseat()
    batch = _pick_batch()
    assert int(batch["gen"]) == 7
    assert batch.get("sealed") is True
    assert batch.get("complete") is True
    by_name = {r["name"]: r for r in doc["instances"]}
    assert by_name["peer_a"]["generation"] == 7
    assert by_name["peer_e"]["generation"] == 4
    assert GEN_LIVE.read_text().strip() == "7"
    assert by_name["peer_a"]["generation"] != 99


def test_p9_jade() -> None:
    """Hold windows change winners across VRIDs without grading hold-file format."""
    doc = _reseat()
    by_name = {r["name"]: r for r in doc["instances"]}
    assert by_name["peer_b"]["state"] == "BACKUP"
    assert by_name["peer_a"]["state"] == "MASTER"
    assert by_name["peer_e"]["state"] == "BACKUP"
    assert by_name["peer_d"]["state"] == "MASTER"

    paths = [OPS / "holds" / "peer_b.hold", REPORT]
    snap = _snapshot_paths(paths)
    try:
        (OPS / "holds" / "peer_b.hold").write_text("until=50\n")
        doc2 = _reseat()
        by2 = {r["name"]: r for r in doc2["instances"]}
        assert by2["peer_b"]["state"] == "MASTER"
        assert by2["peer_a"]["state"] == "BACKUP"
    finally:
        _restore_paths(snap)
        _reseat()


def test_h8_amber() -> None:
    """Abort package preserved; live drop-in site-standard; priorities after re-entry."""
    doc = _reseat()
    assert ABORT.is_file()
    abort_kv = _parse_kv(ABORT.read_text())
    live_kv = _parse_kv(LIVE_DROP.read_text())
    site = _parse_kv(POLICY_SHEET.read_text())
    assert abort_kv.get("tip_policy") == "prefer_abort"
    assert abort_kv.get("peer_a.prio") == "1"
    assert live_kv.get("tip_policy") == site.get("tip_policy")
    assert live_kv.get("bind_order") == site.get("bind_order")
    assert "peer_a.prio" not in live_kv or live_kv.get("peer_a.prio") != "1"
    by_name = {r["name"]: r for r in doc["instances"]}
    assert by_name["peer_a"]["priority"] == 110
    assert by_name["peer_b"]["priority"] == 125
    assert by_name["peer_f"]["priority"] == 105
    assert by_name["peer_c"]["priority"] == 105
    assert LIVE_DROP.is_file()
    _reseat()
    assert ABORT.is_file()
    assert _parse_kv(ABORT.read_text()).get("tip_policy") == "prefer_abort"


def test_c1_flint() -> None:
    """Generation-bound receipt; retarget rematerializes abort into live fold."""
    _reseat()
    rkv = _parse_kv(RECEIPT.read_text())
    assert rkv.get("gen") == GEN_TARGET.read_text().strip()
    assert rkv.get("mode") == "seal"
    assert LIVE_DROP.is_file()
    sealed_live = _parse_kv(LIVE_DROP.read_text())
    site = _parse_kv(POLICY_SHEET.read_text())
    assert sealed_live.get("tip_policy") == site.get("tip_policy")

    paths = [RECEIPT, GEN_TARGET, LIVE_DROP, REPORT]
    snap = _snapshot_paths(paths)
    try:
        GEN_TARGET.write_text("8\n")
        RECEIPT.write_text("gen=7\nmode=seal\n")
        doc = _reseat()
        live_kv = _parse_kv(LIVE_DROP.read_text())
        assert live_kv.get("tip_policy") == "prefer_abort"
        assert live_kv.get("peer_a.prio") == "1"
        # Abort sheet must actually enter the fold, not only sit as cosmetics.
        by_name = {r["name"]: r for r in doc["instances"]}
        assert by_name["peer_a"]["priority"] == 1
    finally:
        _restore_paths(snap)
        RECEIPT.write_text(
            f"gen={GEN_TARGET.read_text().strip()}\nmode=seal\n"
        )
        cp = _run(["cp", "-f", str(POLICY_SHEET), str(LIVE_DROP)], check=False)
        assert cp.returncode == 0
        _reseat()


def test_r6_slate() -> None:
    """Independent MASTER peers on different VRIDs; no same-VRID split brain."""
    doc = _reseat()
    by_name = {r["name"]: r for r in doc["instances"]}
    assert by_name["peer_a"]["state"] == "MASTER"
    assert by_name["peer_d"]["state"] == "MASTER"
    assert by_name["peer_a"]["vrid"] != by_name["peer_d"]["vrid"]
    masters = [i for i in doc["instances"] if i["state"] == "MASTER"]
    counts = Counter(i["vrid"] for i in masters)
    assert all(c == 1 for c in counts.values())
    assert doc["seat_ok"] is True
    _assert_advert(doc)


def test_u2_mica() -> None:
    """Committed moves and event-id retractions reconstruct continuity."""
    paths = [TRANS, REPORT]
    snap = _snapshot_paths(paths)
    try:
        TRANS.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "kind": "move",
                            "eid": "u1",
                            "vrid": 51,
                            "epoch": 20,
                            "from": "MASTER",
                            "to": "BACKUP",
                        },
                        separators=(",", ":"),
                    ),
                    json.dumps(
                        {
                            "kind": "move",
                            "eid": "u2",
                            "vrid": 52,
                            "epoch": 21,
                            "from": "MASTER",
                            "to": "BACKUP",
                        },
                        separators=(",", ":"),
                    ),
                    json.dumps(
                        {"kind": "retract", "eid": "u1", "epoch": 22},
                        separators=(",", ":"),
                    ),
                ]
            )
            + "\n"
        )
        doc = _reseat()
        assert doc["transitions"] == [
            {"vrid": 52, "epoch": 21, "from": "MASTER", "to": "BACKUP"}
        ]
        by_name = {r["name"]: r for r in doc["instances"]}
        assert by_name["peer_a"]["state"] == "MASTER"
        assert by_name["peer_d"]["state"] == "BACKUP"
        assert by_name["peer_f"]["state"] == "BACKUP"
    finally:
        _restore_paths(snap)
        _reseat()


def test_m1_opal() -> None:
    """Eligibility × priority × durable tie-preference × track matrix."""
    doc = _reseat()
    exp = _expected_doc()
    assert doc["instances"] == exp["instances"]
    by_name = {r["name"]: r for r in doc["instances"]}
    assert by_name["peer_b"]["priority"] > by_name["peer_a"]["priority"]
    assert by_name["peer_b"]["state"] == "BACKUP"
    assert by_name["peer_a"]["state"] == "MASTER"
    assert by_name["peer_e"]["priority"] > by_name["peer_d"]["priority"]
    assert by_name["peer_e"]["generation"] < 5
    assert by_name["peer_e"]["state"] == "BACKUP"
    assert by_name["peer_f"]["priority"] == by_name["peer_d"]["priority"]
    assert by_name["peer_d"]["state"] == "MASTER"


def test_k5_garnet() -> None:
    """Retracting one movement leaves a second active movement on the same VRID."""
    paths = [TRANS, REPORT]
    snap = _snapshot_paths(paths)
    try:
        TRANS.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "kind": "move",
                            "eid": "k1",
                            "vrid": 51,
                            "epoch": 30,
                            "from": "MASTER",
                            "to": "BACKUP",
                        },
                        separators=(",", ":"),
                    ),
                    json.dumps(
                        {
                            "kind": "move",
                            "eid": "k2",
                            "vrid": 51,
                            "epoch": 31,
                            "from": "MASTER",
                            "to": "FAULT",
                        },
                        separators=(",", ":"),
                    ),
                    json.dumps(
                        {"kind": "retract", "eid": "k1", "epoch": 32},
                        separators=(",", ":"),
                    ),
                ]
            )
            + "\n"
        )
        doc = _reseat()
        assert doc["transitions"] == [
            {"vrid": 51, "epoch": 31, "from": "MASTER", "to": "FAULT"}
        ]
        by_name = {r["name"]: r for r in doc["instances"]}
        assert by_name["peer_a"]["state"] == "BACKUP"
        assert by_name["peer_c"]["state"] == "BACKUP"
    finally:
        _restore_paths(snap)
        _reseat()


def test_s8_zircon() -> None:
    """Clear output and derived live tables; re-enter and match reconstruction."""
    snap = _snapshot_paths(
        [
            REPORT,
            LIVE / "prio.tsv",
            LIVE / "cand.tsv",
            LIVE / "elig.tsv",
            LIVE / "moves.tsv",
            ADVERT,
        ]
    )
    try:
        REPORT.unlink(missing_ok=True)
        for name in ("prio.tsv", "cand.tsv", "elig.tsv", "moves.tsv"):
            p = LIVE / name
            if p.exists():
                p.unlink()
        if ADVERT.exists():
            ADVERT.unlink()
        doc = _reseat()
        exp = _expected_doc()
        assert doc == exp
        _assert_advert(doc)
    finally:
        _restore_paths(snap)
        _reseat()


def test_t4_pearl() -> None:
    """Surface MASTER-OK is insufficient; deep ledger and advert still graded."""
    doc = _reseat()
    assert doc["seat_ok"] is True
    health = _run(["/usr/local/bin/vrrphealth"], check=False)
    assert health.returncode == 0
    assert health.stdout.strip() == "MASTER-OK"
    masters = [i for i in doc["instances"] if i["state"] == "MASTER"]
    counts = Counter(i["vrid"] for i in masters)
    assert all(c == 1 for c in counts.values())
    token = (ETC / "runtime" / "token.map").read_text()
    assert token.count("MASTER") >= 2
    assert {i["name"] for i in masters} == {"peer_a", "peer_d"}
    _assert_advert(doc)
    assert "peer_b" not in ADVERT.read_text()


def test_b6_cobalt() -> None:
    """Scoped replace/delta lexical order changes rankings on two VRIDs."""
    paths = [ETC / "conf.d" / "80-inject.conf", REPORT]
    snap = _snapshot_paths(paths)
    try:
        (ETC / "conf.d" / "80-inject.conf").write_text(
            "delta peer_c.prio=30\nreplace peer_f.prio=200\n"
        )
        doc = _reseat()
        by_name = {r["name"]: r for r in doc["instances"]}
        # fold 105+30=135; track DOWN so no extra
        assert by_name["peer_c"]["priority"] == 135
        assert by_name["peer_c"]["state"] == "MASTER"
        assert by_name["peer_a"]["state"] == "BACKUP"
        # replace 200 then track UP +10 → 210
        assert by_name["peer_f"]["priority"] == 210
        assert by_name["peer_f"]["state"] == "MASTER"
        assert by_name["peer_d"]["state"] == "BACKUP"
    finally:
        _restore_paths(snap)
        inj = ETC / "conf.d" / "80-inject.conf"
        if inj.exists():
            inj.unlink()
        _reseat()


def test_d4_jet() -> None:
    """New sealed generation with tie, below-floor peer, and hold boundary."""
    paths = [
        PREFER,
        GEN_TARGET,
        RECEIPT,
        OPS / "holds" / "peer_a.hold",
        OPS / "holds" / "peer_b.hold",
        ETC / "conf.d" / "85-tie.conf",
        LIVE_DROP,
        REPORT,
    ]
    snap = _snapshot_paths(paths)
    try:
        PREFER.write_text(
            PREFER.read_text()
            + json.dumps(
                {
                    "kind": "batch",
                    "id": "b11",
                    "gen": 11,
                    "sealed": True,
                    "complete": True,
                    "rows": [
                        {"id": "peer_a", "tip": 11, "rank": 0},
                        {"id": "peer_b", "tip": 11, "rank": 0},
                        {"id": "peer_c", "tip": 2, "rank": 5},
                        {"id": "peer_d", "tip": 11, "rank": 3},
                        {"id": "peer_e", "tip": 11, "rank": 1},
                        {"id": "peer_f", "tip": 11, "rank": 0},
                    ],
                },
                separators=(",", ":"),
            )
            + "\n"
        )
        GEN_TARGET.write_text("11\n")
        RECEIPT.write_text("gen=11\nmode=seal\n")
        (OPS / "holds" / "peer_a.hold").write_text("until=1000\n")
        (OPS / "holds" / "peer_b.hold").write_text("until=50\n")
        (ETC / "conf.d" / "85-tie.conf").write_text("replace peer_d.prio=120\n")
        doc = _reseat()
        by_name = {r["name"]: r for r in doc["instances"]}
        assert by_name["peer_a"]["state"] == "BACKUP"
        assert by_name["peer_b"]["state"] == "MASTER"
        assert by_name["peer_c"]["generation"] == 2
        assert by_name["peer_c"]["state"] == "BACKUP"
        assert by_name["peer_d"]["priority"] == 120
        # peer_e folded 120; no UP track
        assert by_name["peer_e"]["priority"] == 120
        assert by_name["peer_d"]["state"] == "MASTER"
        assert by_name["peer_e"]["state"] == "BACKUP"
    finally:
        _restore_paths(snap)
        ha = OPS / "holds" / "peer_a.hold"
        if ha.exists() and snap.get(str(ha)) is None:
            ha.unlink()
        tie = ETC / "conf.d" / "85-tie.conf"
        if tie.exists() and snap.get(str(tie)) is None:
            tie.unlink()
        _run(["cp", "-f", str(POLICY_SHEET), str(LIVE_DROP)], check=False)
        if not RECEIPT.exists() or _parse_kv(RECEIPT.read_text()).get("gen") != GEN_TARGET.read_text().strip():
            RECEIPT.write_text(f"gen={GEN_TARGET.read_text().strip()}\nmode=seal\n")
        _reseat()


def test_x7_agate() -> None:
    """Interleaved moves/retractions; retraction naming another VRID's event."""
    paths = [TRANS, REPORT]
    snap = _snapshot_paths(paths)
    try:
        TRANS.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "kind": "move",
                            "eid": "x1",
                            "vrid": 51,
                            "epoch": 40,
                            "from": "MASTER",
                            "to": "BACKUP",
                        },
                        separators=(",", ":"),
                    ),
                    json.dumps(
                        {
                            "kind": "move",
                            "eid": "x2",
                            "vrid": 52,
                            "epoch": 41,
                            "from": "MASTER",
                            "to": "BACKUP",
                        },
                        separators=(",", ":"),
                    ),
                    json.dumps(
                        {"kind": "retract", "eid": "x2", "epoch": 42},
                        separators=(",", ":"),
                    ),
                    json.dumps(
                        {
                            "kind": "move",
                            "eid": "x3",
                            "vrid": 52,
                            "epoch": 43,
                            "from": "BACKUP",
                            "to": "FAULT",
                        },
                        separators=(",", ":"),
                    ),
                ]
            )
            + "\n"
        )
        doc = _reseat()
        assert {"vrid": 51, "epoch": 40, "from": "MASTER", "to": "BACKUP"} in doc[
            "transitions"
        ]
        assert {"vrid": 52, "epoch": 43, "from": "BACKUP", "to": "FAULT"} in doc[
            "transitions"
        ]
        assert not any(t["vrid"] == 52 and t["from"] == "MASTER" for t in doc["transitions"])
        by_name = {r["name"]: r for r in doc["instances"]}
        assert by_name["peer_a"]["state"] == "BACKUP"
        assert by_name["peer_d"]["state"] == "MASTER"
    finally:
        _restore_paths(snap)
        _reseat()


def test_y2_onyx() -> None:
    """Track probe UP/DOWN polarity changes effective priority and winners."""
    paths = [
        TRACK / "peer_c.status",
        TRACK / "peer_f.status",
        REPORT,
        ADVERT,
    ]
    snap = _snapshot_paths(paths)
    try:
        (TRACK / "peer_c.status").write_text("UP\n")
        (TRACK / "peer_f.status").write_text("DOWN\n")
        doc = _reseat()
        by_name = {r["name"]: r for r in doc["instances"]}
        # peer_c 105+30=135 becomes MASTER on 51
        assert by_name["peer_c"]["priority"] == 135
        assert by_name["peer_c"]["state"] == "MASTER"
        assert by_name["peer_a"]["state"] == "BACKUP"
        # peer_f loses UP boost → 95; peer_d 105 stays MASTER on 52
        assert by_name["peer_f"]["priority"] == 95
        assert by_name["peer_d"]["state"] == "MASTER"
        _assert_advert(doc)
    finally:
        _restore_paths(snap)
        _reseat()


def test_z9_spinel() -> None:
    """Interface generation below floor keeps a high-priority peer ineligible."""
    paths = [NETIF / "peer_d.gen", OPS / "holds" / "peer_e.hold", REPORT]
    snap = _snapshot_paths(paths)
    try:
        (NETIF / "peer_d.gen").write_text("2\n")
        # raise peer_e tip eligibility path: tip already 4 < 5, so bump via prefer inject
        # Instead clear peer_e floor trap by giving tip room — use hold inactive and
        # temporarily lower peer_e floor via... floors are separate. Raise tip through
        # prefer rewrite would be large. Simpler: peer_d netif low → peer_f (105) wins 52.
        doc = _reseat()
        by_name = {r["name"]: r for r in doc["instances"]}
        assert by_name["peer_d"]["state"] == "BACKUP"
        assert by_name["peer_f"]["state"] == "MASTER"
        assert by_name["peer_f"]["priority"] == 105
        _assert_advert(doc)
    finally:
        _restore_paths(snap)
        _reseat()
