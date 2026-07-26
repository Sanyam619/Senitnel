"""Verifier for Consul service intentions seating."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

REPORT = Path("/output/consul-seat.json")
DEF_D = Path("/app/data/consul")
EXTRA_D = Path("/var/lib/consul/ops/extra")
PIN = Path("/app/packaging/consul.sha256")
SITE_SHEET = Path("/app/config/site_standard.conf")
PUBLISHER = Path("/app/publisher/consulseat")
ENTRY = "/app/ops/run_consul_seat.sh"

ETC = Path("/etc/consul.d")
CONF_D = ETC / "conf.d"
MESH_D = ETC / "intentions.d"
CATALOG = ETC / "runtime" / "catalog.map"
TOKEN = ETC / "runtime" / "token.map"
LIVE_DROP = CONF_D / "90-local.hcl"

OPS = Path("/var/lib/consul/ops")
ROSTER = OPS / "roster.jsonl"
PREFER = OPS / "prefer.jsonl"
INTENTS = OPS / "intents.jsonl"
SUPERSEDED = OPS / "superseded.list"
MIRROR = OPS / "mirror" / "roster_mirror.jsonl"
FLOORS = OPS / "floors"
ABORT = OPS / "abort.d" / "90-local.hcl"
LIVE = OPS / "live"
RECEIPT = OPS / "state" / "cutover.ok"
GEN_TARGET = OPS / "state" / "generation.target"
GEN_LIVE = OPS / "state" / "generation.live"


def _run(cmd: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def _reseat() -> dict:
    REPORT.unlink(missing_ok=True)
    proc = _run(["/bin/bash", ENTRY], check=False)
    assert proc.returncode == 0, f"seat failed: {proc.stderr}\n{proc.stdout}"
    assert REPORT.is_file(), "missing /output/consul-seat.json"
    return json.loads(REPORT.read_text())


def _parse_kv(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, val = line.split("=", 1)
        out[key.strip()] = val.strip()
    return out


def _jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.is_file():
        return rows
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def _load_defs() -> dict[str, str]:
    defs: dict[str, str] = {}
    roots = [DEF_D]
    if EXTRA_D.is_dir():
        roots.append(EXTRA_D)
    for root in roots:
        for f in sorted(root.glob("*.json")):
            svc = json.loads(f.read_text()).get("service", {})
            if svc.get("name"):
                defs[svc["name"]] = svc.get("node", "")
    return defs


def _fold_bind() -> dict[str, str]:
    seat: dict[str, str] = {}
    held: set[str] = set()
    for f in sorted(CONF_D.glob("*.hcl")):
        for raw in f.read_text().splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            mode = "plain"
            if line.startswith("pin "):
                line, mode = line[len("pin ") :].strip(), "hold"
            elif line.startswith("drop "):
                line, mode = line[len("drop ") :].strip(), "clear"
            if mode == "clear":
                key = line.replace(" ", "")
                if not key.endswith(".node"):
                    continue
                name = key[: -len(".node")]
                if name in held:
                    continue
                seat.pop(name, None)
                continue
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            key, val = key.strip(), val.strip()
            if not key.endswith(".node"):
                continue
            name = key[: -len(".node")]
            if name in held:
                continue
            seat[name] = val
            if mode == "hold":
                held.add(name)
    return seat


def _superseded() -> set[str]:
    gone: set[str] = set()
    if not SUPERSEDED.is_file():
        return gone
    for raw in SUPERSEDED.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            gone.add(line)
    return gone


def _pick_tip() -> dict:
    gone = _superseded()
    live = [
        row
        for row in _jsonl(ROSTER)
        if row.get("kind") == "batch"
        and row.get("sealed") is True
        and row.get("complete") is True
        and row.get("id") not in gone
    ]
    assert live, "no eligible catalog batch"
    live.sort(key=lambda r: int(r.get("gen", -1)))
    return live[-1]


def _pick_prefer(gen: int) -> dict | None:
    live = [
        row
        for row in _jsonl(PREFER)
        if row.get("kind") == "batch"
        and int(row.get("gen", -1)) == gen
        and row.get("sealed") is True
        and row.get("complete") is True
    ]
    if not live:
        return None
    live.sort(key=lambda r: int(r.get("gen", -1)))
    return live[-1]


def _standing_pairs() -> set[tuple[str, str]]:
    held: dict[str, dict] = {}
    for row in _jsonl(INTENTS):
        eid = row.get("eid")
        if not eid:
            continue
        if row.get("kind") == "commit":
            held[eid] = row
        elif row.get("kind") == "retract":
            held.pop(eid, None)
    return {(row["source"], row["destination"]) for row in held.values()}


def _floor(name: str) -> int:
    f = FLOORS / f"{name}.floor"
    return int(f.read_text().strip()) if f.is_file() else 0


def _finite_int(v: object) -> bool:
    return isinstance(v, int) and float("-inf") < float(v) < float("inf")


def _expected_doc() -> dict:
    defs = _load_defs()
    bind = _fold_bind()
    tip = _pick_tip()
    tip_node = {r["name"]: r["node"] for r in tip.get("rows", [])}
    tip_gen = {r["name"]: int(r["gen"]) for r in tip.get("rows", [])}

    names = sorted(set(defs) | set(bind) | set(tip_node))
    services = []
    registered: dict[str, bool] = {}
    for name in names:
        node = bind.get(name, defs.get(name, ""))
        gen = tip_gen.get(name, 0)
        ok = (
            name in tip_node
            and node == tip_node[name]
            and gen >= _floor(name)
        )
        registered[name] = ok
        services.append(
            {"name": name, "node": node, "generation": gen, "registered": ok}
        )

    batch = _pick_prefer(int(tip.get("gen", 0)))
    standing = _standing_pairs()
    intentions = []
    if batch is not None:
        rows = sorted(
            batch.get("rows", []), key=lambda r: (r["source"], r["destination"])
        )
        for row in rows:
            src, dst = row["source"], row["destination"]
            intentions.append(
                {
                    "source": src,
                    "destination": dst,
                    "action": row["action"],
                    "honored": (src, dst) in standing
                    and registered.get(src, False)
                    and registered.get(dst, False),
                }
            )

    receipt = _parse_kv(RECEIPT.read_text()) if RECEIPT.is_file() else {}
    seat_ok = (
        receipt.get("gen") == GEN_TARGET.read_text().strip()
        and receipt.get("mode") == "seal"
        and any(registered.values())
    )
    return {
        "schema_tag": "consul-seat-v1",
        "services": services,
        "intentions": intentions,
        "seat_ok": seat_ok,
    }


def _snapshot(paths: list[Path]) -> dict[str, bytes | None]:
    return {str(p): (p.read_bytes() if p.is_file() else None) for p in paths}


def _restore(snap: dict[str, bytes | None]) -> None:
    for path_s, data in snap.items():
        p = Path(path_s)
        if data is None:
            if p.is_file():
                p.unlink()
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)


def _sha256(path: Path) -> str:
    proc = _run(["sha256sum", str(path)], check=False)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.split()[0]


def _pins() -> tuple[dict[str, str], str]:
    assert PIN.is_file(), "missing integrity pin file"
    defs: dict[str, str] = {}
    publisher = ""
    for raw in PIN.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        digest, path = line.split(None, 1)
        path = path.strip()
        if path.endswith("consulseat"):
            publisher = digest
        else:
            defs[Path(path).name] = digest
    assert defs, "no pinned definitions"
    assert publisher, "no pinned publisher"
    return defs, publisher


def _assert_pins() -> None:
    defs, publisher = _pins()
    for name, digest in defs.items():
        assert _sha256(DEF_D / name) == digest, f"{name} was rewritten"
    assert _sha256(PUBLISHER) == publisher, "publisher was rewritten"


def _assert_catalog(doc: dict) -> None:
    assert CATALOG.is_file(), "missing /etc/consul.d/runtime/catalog.map"
    expected = [
        f"{row['name']}={row['node']}" for row in doc["services"] if row["registered"]
    ]
    got = [line for line in CATALOG.read_text().splitlines() if line.strip()]
    assert got == sorted(expected), f"catalog.map {got} != {sorted(expected)}"


def _by_name(doc: dict) -> dict[str, dict]:
    return {row["name"]: row for row in doc["services"]}


def _by_pair(doc: dict) -> dict[tuple[str, str], dict]:
    return {(row["source"], row["destination"]): row for row in doc["intentions"]}


def test_q3_topaz() -> None:
    """Baseline ledger shape, reconstruction match, and deep catalog ownership."""
    doc = _reseat()
    exp = _expected_doc()
    assert doc["schema_tag"] == "consul-seat-v1"
    assert isinstance(doc["services"], list)
    assert isinstance(doc["intentions"], list)
    assert isinstance(doc["seat_ok"], bool)
    for row in doc["services"]:
        assert {"name", "node", "generation", "registered"} <= set(row)
        assert isinstance(row["name"], str)
        assert isinstance(row["node"], str)
        assert _finite_int(row["generation"])
        assert isinstance(row["registered"], bool)
    for row in doc["intentions"]:
        assert {"source", "destination", "action", "honored"} <= set(row)
        assert isinstance(row["source"], str)
        assert isinstance(row["destination"], str)
        assert row["action"] in {"allow", "deny"}
        assert isinstance(row["honored"], bool)
    assert doc["services"] == exp["services"]
    assert doc["intentions"] == exp["intentions"]
    assert doc["seat_ok"] is True
    svc = _by_name(doc)
    assert svc["alpha"] == {
        "name": "alpha",
        "node": "node-a1",
        "generation": 7,
        "registered": True,
    }
    assert svc["iota"]["generation"] == 0
    assert svc["iota"]["registered"] is False
    _assert_catalog(doc)
    _assert_pins()


def test_n4_beryl() -> None:
    """Repeated passes are byte-identical and leave the selected generation stable."""
    _reseat()
    first = REPORT.read_bytes()
    live_first = GEN_LIVE.read_text().strip()
    _reseat()
    second = REPORT.read_bytes()
    live_second = GEN_LIVE.read_text().strip()
    assert first == second
    assert first.endswith(b"\n")
    assert live_first == live_second == "7"
    receipt = _parse_kv(RECEIPT.read_text())
    assert receipt.get("gen") == GEN_TARGET.read_text().strip()
    assert receipt.get("mode") == "seal"


def test_v5_coral() -> None:
    """Unsealed, incomplete, superseded, and mirrored batches are never the tip."""
    doc = _reseat()
    tip = _pick_tip()
    assert tip["id"] == "r7"
    assert GEN_LIVE.read_text().strip() == "7"
    ids = {row.get("id") for row in _jsonl(ROSTER) if row.get("kind") == "batch"}
    assert {"r8", "r9", "r12"} <= ids
    svc = _by_name(doc)
    assert svc["epsilon"]["generation"] == 3
    assert svc["theta"]["generation"] == 2
    assert svc["gamma"]["generation"] == 6
    assert all(row["generation"] != 12 for row in doc["services"])
    assert svc["delta"]["node"] == "node-d9"
    assert svc["delta"]["registered"] is False
    mirror = _jsonl(MIRROR)
    assert mirror and int(mirror[0]["gen"]) == 7
    assert {r["name"]: r["node"] for r in mirror[0]["rows"]}["delta"] == "node-d9"
    assert svc["iota"]["registered"] is False


def test_w7_quartz() -> None:
    """Staged extra definition plus a late drop-in seat under a novel sealed batch."""
    _assert_pins()
    snap = _snapshot([ROSTER, PREFER, INTENTS, REPORT])
    extra_def = EXTRA_D / "kappa.json"
    late = CONF_D / "70-extra.hcl"
    try:
        EXTRA_D.mkdir(parents=True, exist_ok=True)
        extra_def.write_text(
            json.dumps(
                {
                    "service": {
                        "name": "kappa",
                        "id": "kappa-1",
                        "node": "node-k4",
                        "port": 8110,
                        "tags": ["mesh"],
                    }
                }
            )
            + "\n"
        )
        late.write_text("pin kappa.node = node-k1\ndrop epsilon.node\n")
        rows = [
            {"name": "alpha", "node": "node-a1", "gen": 13},
            {"name": "beta", "node": "node-b2", "gen": 13},
            {"name": "gamma", "node": "node-c3", "gen": 13},
            {"name": "delta", "node": "node-d4", "gen": 13},
            {"name": "epsilon", "node": "node-e5", "gen": 13},
            {"name": "zeta", "node": "node-f6", "gen": 13},
            {"name": "eta", "node": "node-g7", "gen": 13},
            {"name": "theta", "node": "node-h8", "gen": 13},
            {"name": "iota", "node": "node-i9", "gen": 13},
            {"name": "kappa", "node": "node-k1", "gen": 13},
        ]
        with ROSTER.open("a") as fh:
            fh.write(
                json.dumps(
                    {
                        "kind": "batch",
                        "id": "r13",
                        "gen": 13,
                        "sealed": True,
                        "complete": True,
                        "rows": rows,
                    },
                    separators=(",", ":"),
                )
                + "\n"
            )
        with PREFER.open("a") as fh:
            fh.write(
                json.dumps(
                    {
                        "kind": "batch",
                        "id": "p13",
                        "gen": 13,
                        "sealed": True,
                        "complete": True,
                        "rows": [
                            {
                                "source": "kappa",
                                "destination": "beta",
                                "action": "allow",
                            },
                            {
                                "source": "gamma",
                                "destination": "eta",
                                "action": "deny",
                            },
                            {
                                "source": "zeta",
                                "destination": "iota",
                                "action": "allow",
                            },
                        ],
                    },
                    separators=(",", ":"),
                )
                + "\n"
            )
        with INTENTS.open("a") as fh:
            fh.write(
                json.dumps(
                    {
                        "kind": "commit",
                        "eid": "c30",
                        "source": "kappa",
                        "destination": "beta",
                        "epoch": 40,
                    },
                    separators=(",", ":"),
                )
                + "\n"
            )
        doc = _reseat()
        assert doc == _expected_doc()
        assert GEN_LIVE.read_text().strip() == "13"
        svc = _by_name(doc)
        assert svc["kappa"]["node"] == "node-k1"
        assert svc["kappa"]["registered"] is True
        assert svc["epsilon"]["node"] == "node-e5"
        assert svc["epsilon"]["registered"] is True
        assert svc["delta"]["registered"] is False
        pairs = _by_pair(doc)
        assert pairs[("kappa", "beta")]["action"] == "allow"
        assert pairs[("kappa", "beta")]["honored"] is True
        assert pairs[("gamma", "eta")]["honored"] is False
        assert pairs[("zeta", "iota")]["honored"] is True
        assert set(pairs) == {("gamma", "eta"), ("kappa", "beta"), ("zeta", "iota")}
        assert doc["seat_ok"] is True
        _assert_catalog(doc)
        _assert_pins()
    finally:
        _restore(snap)
        if late.is_file():
            late.unlink()
        if EXTRA_D.is_dir():
            shutil.rmtree(EXTRA_D)
        _reseat()


def test_p9_jade() -> None:
    """Floor comparison is inclusive and a raised floor drops deep ownership."""
    doc = _reseat()
    svc = _by_name(doc)
    assert svc["theta"]["generation"] == _floor("theta") == 2
    assert svc["theta"]["registered"] is True
    assert svc["epsilon"]["generation"] == 3
    assert _floor("epsilon") == 5
    assert svc["epsilon"]["registered"] is False
    assert "theta=node-h8" in CATALOG.read_text().splitlines()

    snap = _snapshot([FLOORS / "theta.floor", REPORT])
    try:
        (FLOORS / "theta.floor").write_text("3\n")
        doc2 = _reseat()
        assert doc2 == _expected_doc()
        svc2 = _by_name(doc2)
        assert svc2["theta"]["node"] == "node-h8"
        assert svc2["theta"]["generation"] == 2
        assert svc2["theta"]["registered"] is False
        assert "theta=node-h8" not in CATALOG.read_text().splitlines()
        assert doc2["seat_ok"] is True
        _assert_catalog(doc2)
    finally:
        _restore(snap)
        _reseat()


def test_h8_amber() -> None:
    """Rollback package stays forensic while live bindings follow durable authority."""
    doc = _reseat()
    assert ABORT.is_file()
    abort_kv = _parse_kv(ABORT.read_text())
    assert abort_kv.get("tip_policy") == "prefer_abort"
    assert abort_kv.get("alpha.node") == "node-a9"
    assert abort_kv.get("beta.node") == "node-b9"
    assert LIVE_DROP.is_file()
    live_kv = _parse_kv(LIVE_DROP.read_text())
    site_kv = _parse_kv(SITE_SHEET.read_text())
    assert live_kv.get("tip_policy") == site_kv.get("tip_policy") == "durable"
    assert live_kv.get("bind_order") == site_kv.get("bind_order") == "lexical"
    assert "alpha.node" not in live_kv
    assert "beta.node" not in live_kv
    svc = _by_name(doc)
    assert svc["alpha"]["node"] == "node-a1"
    assert svc["beta"]["node"] == "node-b2"
    assert svc["alpha"]["registered"] is True
    assert svc["beta"]["registered"] is True
    _reseat()
    assert ABORT.is_file()
    assert _parse_kv(ABORT.read_text()).get("alpha.node") == "node-a9"
    assert _parse_kv(LIVE_DROP.read_text()).get("tip_policy") == "durable"


def test_c1_flint() -> None:
    """A receipt behind the target generation reseats rollback bindings into the fold."""
    _reseat()
    assert _parse_kv(RECEIPT.read_text()).get("gen") == "7"
    snap = _snapshot([RECEIPT, GEN_TARGET, LIVE_DROP, REPORT])
    try:
        GEN_TARGET.write_text("9\n")
        RECEIPT.write_text("gen=7\nmode=seal\n")
        doc = _reseat()
        live_kv = _parse_kv(LIVE_DROP.read_text())
        assert live_kv.get("tip_policy") == "prefer_abort"
        assert live_kv.get("alpha.node") == "node-a9"
        svc = _by_name(doc)
        assert svc["alpha"]["node"] == "node-a9"
        assert svc["alpha"]["registered"] is False
        assert svc["beta"]["node"] == "node-b9"
        assert svc["beta"]["registered"] is False
        assert doc["seat_ok"] is False
        pairs = _by_pair(doc)
        assert pairs[("alpha", "beta")]["honored"] is False
        assert pairs[("beta", "zeta")]["honored"] is False
        assert "alpha=node-a1" not in CATALOG.read_text().splitlines()
        assert _parse_kv(RECEIPT.read_text()) == {"gen": "9", "mode": "seal"}
    finally:
        _restore(snap)
        _run(["cp", "-f", str(SITE_SHEET), str(LIVE_DROP)], check=False)
        RECEIPT.write_text(f"gen={GEN_TARGET.read_text().strip()}\nmode=seal\n")
        _reseat()


def test_r6_slate() -> None:
    """Pinned bindings hold and dropped bindings fall back to the frozen definition."""
    doc = _reseat()
    svc = _by_name(doc)
    assert svc["theta"]["node"] == "node-h8"
    assert svc["gamma"]["node"] == "node-c3"
    assert svc["gamma"]["registered"] is True
    assert svc["epsilon"]["node"] == "node-e7"
    assert svc["zeta"]["node"] == "node-f6"
    assert _fold_bind().get("gamma") is None

    snap = _snapshot([REPORT])
    late = CONF_D / "80-late.hcl"
    try:
        late.write_text("theta.node = node-h1\ngamma.node = node-c9\n")
        doc2 = _reseat()
        assert doc2 == _expected_doc()
        svc2 = _by_name(doc2)
        assert svc2["theta"]["node"] == "node-h8"
        assert svc2["theta"]["registered"] is True
        assert svc2["gamma"]["node"] == _fold_bind()["gamma"]
        assert svc2["gamma"]["node"] != svc["gamma"]["node"]
        assert svc2["gamma"]["registered"] is False
        assert "gamma=node-c3" not in CATALOG.read_text().splitlines()
        _assert_catalog(doc2)
    finally:
        if late.is_file():
            late.unlink()
        _restore(snap)
        _reseat()


def test_u2_mica() -> None:
    """A retraction cancels one event id and leaves other commits standing."""
    doc = _reseat()
    pairs = _by_pair(doc)
    assert pairs[("alpha", "gamma")]["honored"] is True
    assert pairs[("gamma", "eta")]["honored"] is False

    snap = _snapshot([INTENTS, REPORT])
    try:
        INTENTS.write_text(
            "\n".join(
                json.dumps(row, separators=(",", ":"))
                for row in [
                    {
                        "kind": "commit",
                        "eid": "c1",
                        "source": "alpha",
                        "destination": "beta",
                        "epoch": 10,
                    },
                    {
                        "kind": "commit",
                        "eid": "c2",
                        "source": "alpha",
                        "destination": "gamma",
                        "epoch": 11,
                    },
                    {
                        "kind": "commit",
                        "eid": "c9",
                        "source": "alpha",
                        "destination": "gamma",
                        "epoch": 18,
                    },
                    {"kind": "retract", "eid": "c9", "epoch": 19},
                    {"kind": "retract", "eid": "zz", "epoch": 20},
                    {
                        "kind": "commit",
                        "eid": "c7",
                        "source": "eta",
                        "destination": "theta",
                        "epoch": 21,
                    },
                ]
            )
            + "\n"
        )
        doc2 = _reseat()
        assert doc2 == _expected_doc()
        pairs2 = _by_pair(doc2)
        assert pairs2[("alpha", "beta")]["honored"] is True
        assert pairs2[("alpha", "gamma")]["honored"] is True
        assert pairs2[("eta", "theta")]["honored"] is True
        assert pairs2[("beta", "zeta")]["honored"] is False
        assert pairs2[("zeta", "iota")]["honored"] is False
        assert [row["honored"] for row in doc2["intentions"]].count(True) == 3
    finally:
        _restore(snap)
        _reseat()


def test_m1_opal() -> None:
    """Published actions follow the durable preference, not the permissive surface."""
    doc = _reseat()
    surface = MESH_D / "50-mesh.hcl"
    assert surface.is_file()
    text = surface.read_text()
    assert "default_action = allow" in text
    assert text.count("= allow") >= 9
    pairs = _by_pair(doc)
    assert pairs[("alpha", "beta")]["action"] == "deny"
    assert pairs[("alpha", "gamma")]["action"] == "allow"
    assert pairs[("beta", "zeta")]["action"] == "allow"
    assert pairs[("delta", "beta")]["action"] == "allow"
    assert pairs[("epsilon", "zeta")]["action"] == "deny"
    assert pairs[("eta", "theta")]["action"] == "allow"
    assert pairs[("gamma", "eta")]["action"] == "deny"
    assert pairs[("zeta", "iota")]["action"] == "deny"
    assert [row["action"] for row in doc["intentions"]].count("deny") == 4
    batch = _pick_prefer(7)
    assert batch is not None
    assert batch["id"] == "p7"


def test_k5_garnet() -> None:
    """A newer sealed generation moves registration and honoring together."""
    snap = _snapshot([ROSTER, PREFER, INTENTS, REPORT])
    try:
        with ROSTER.open("a") as fh:
            fh.write(
                json.dumps(
                    {
                        "kind": "batch",
                        "id": "r10",
                        "gen": 10,
                        "sealed": True,
                        "complete": True,
                        "rows": [
                            {"name": "alpha", "node": "node-a1", "gen": 10},
                            {"name": "beta", "node": "node-b2", "gen": 10},
                            {"name": "gamma", "node": "node-c3", "gen": 4},
                            {"name": "delta", "node": "node-d9", "gen": 10},
                            {"name": "epsilon", "node": "node-e5", "gen": 10},
                            {"name": "zeta", "node": "node-f6", "gen": 10},
                            {"name": "eta", "node": "node-g7", "gen": 10},
                            {"name": "theta", "node": "node-h9", "gen": 10},
                            {"name": "iota", "node": "node-i9", "gen": 10},
                        ],
                    },
                    separators=(",", ":"),
                )
                + "\n"
            )
            fh.write(
                json.dumps(
                    {
                        "kind": "batch",
                        "id": "r11",
                        "gen": 11,
                        "sealed": True,
                        "complete": False,
                        "rows": [{"name": "alpha", "node": "node-a1", "gen": 11}],
                    },
                    separators=(",", ":"),
                )
                + "\n"
            )
        with PREFER.open("a") as fh:
            fh.write(
                json.dumps(
                    {
                        "kind": "batch",
                        "id": "p10",
                        "gen": 10,
                        "sealed": True,
                        "complete": True,
                        "rows": [
                            {
                                "source": "alpha",
                                "destination": "beta",
                                "action": "allow",
                            },
                            {
                                "source": "delta",
                                "destination": "beta",
                                "action": "allow",
                            },
                            {
                                "source": "eta",
                                "destination": "theta",
                                "action": "deny",
                            },
                            {
                                "source": "iota",
                                "destination": "alpha",
                                "action": "deny",
                            },
                            {
                                "source": "zeta",
                                "destination": "iota",
                                "action": "allow",
                            },
                        ],
                    },
                    separators=(",", ":"),
                )
                + "\n"
            )
        with INTENTS.open("a") as fh:
            fh.write(
                json.dumps(
                    {
                        "kind": "commit",
                        "eid": "c20",
                        "source": "iota",
                        "destination": "alpha",
                        "epoch": 30,
                    },
                    separators=(",", ":"),
                )
                + "\n"
            )
        doc = _reseat()
        assert doc == _expected_doc()
        assert GEN_LIVE.read_text().strip() == "10"
        svc = _by_name(doc)
        assert svc["delta"]["registered"] is True
        assert svc["iota"]["registered"] is True
        assert svc["gamma"]["generation"] == 4
        assert svc["gamma"]["registered"] is True
        assert svc["epsilon"]["node"] == "node-e7"
        assert svc["epsilon"]["registered"] is False
        assert svc["theta"]["node"] == "node-h8"
        assert svc["theta"]["generation"] == 10
        assert svc["theta"]["registered"] is False
        pairs = _by_pair(doc)
        assert pairs[("delta", "beta")]["honored"] is True
        assert pairs[("zeta", "iota")]["honored"] is True
        assert pairs[("iota", "alpha")]["honored"] is True
        assert pairs[("eta", "theta")]["honored"] is False
        assert doc["seat_ok"] is True
        _assert_catalog(doc)
    finally:
        _restore(snap)
        _reseat()


def test_d4_jet() -> None:
    """Reinstating a withdrawn batch id moves the tip and its preference together."""
    snap = _snapshot([SUPERSEDED, REPORT])
    try:
        SUPERSEDED.write_text("# withdrawn while the rollout was aborted\nr3\n")
        doc = _reseat()
        assert doc == _expected_doc()
        assert _pick_tip()["id"] == "r8"
        assert GEN_LIVE.read_text().strip() == "8"
        assert all(row["generation"] == 8 for row in doc["services"])
        assert all(row["registered"] for row in doc["services"])
        pairs = _by_pair(doc)
        assert pairs[("alpha", "beta")]["action"] == "allow"
        assert pairs[("delta", "beta")]["action"] == "deny"
        assert pairs[("epsilon", "zeta")]["action"] == "allow"
        assert pairs[("gamma", "eta")]["action"] == "allow"
        assert pairs[("gamma", "eta")]["honored"] is False
        assert [row["honored"] for row in doc["intentions"]].count(True) == 7
        assert len(CATALOG.read_text().splitlines()) == 9
        assert doc["seat_ok"] is True
    finally:
        _restore(snap)
        _reseat()


def test_s8_zircon() -> None:
    """Cleared work tables and a hand-written ledger do not survive a seating pass."""
    snap = _snapshot(
        [
            REPORT,
            CATALOG,
            LIVE / "bind.tsv",
            LIVE / "tip.tsv",
            LIVE / "reg.tsv",
            LIVE / "acts.tsv",
            LIVE / "cmt.tsv",
        ]
    )
    try:
        for name in ("bind.tsv", "tip.tsv", "reg.tsv", "acts.tsv", "cmt.tsv"):
            p = LIVE / name
            if p.is_file():
                p.unlink()
        if CATALOG.is_file():
            CATALOG.unlink()
        doc = _reseat()
        exp = _expected_doc()
        assert doc == exp
        _assert_catalog(doc)

        REPORT.write_text(
            json.dumps(
                {
                    "schema_tag": "consul-seat-v1",
                    "services": [
                        {
                            "name": row["name"],
                            "node": row["node"],
                            "generation": 99,
                            "registered": True,
                        }
                        for row in exp["services"]
                    ],
                    "intentions": [
                        {
                            "source": row["source"],
                            "destination": row["destination"],
                            "action": "allow",
                            "honored": True,
                        }
                        for row in exp["intentions"]
                    ],
                    "seat_ok": True,
                }
            )
            + "\n"
        )
        proc = _run(["/bin/bash", ENTRY], check=False)
        assert proc.returncode == 0, proc.stderr
        again = json.loads(REPORT.read_text())
        assert again == exp
        assert [row["registered"] for row in again["services"]].count(True) == 6
    finally:
        _restore(snap)
        _reseat()


def test_t4_pearl() -> None:
    """Surface passing health and token rows do not stand in for deep seating."""
    doc = _reseat()
    health = _run(["/usr/local/bin/consulhealth"], check=False)
    assert health.returncode == 0
    assert health.stdout.strip() == "catalog-passing"
    token_rows = [
        line for line in TOKEN.read_text().splitlines() if line.strip()
    ]
    assert len(token_rows) == 9
    assert all(row.endswith(" passing") for row in token_rows)
    svc = _by_name(doc)
    assert [row["registered"] for row in doc["services"]].count(True) == 6
    for name in ("delta", "epsilon", "iota"):
        assert svc[name]["registered"] is False
        assert f"{name}=" not in CATALOG.read_text()
    assert [row["honored"] for row in doc["intentions"]].count(True) == 4
    assert doc["seat_ok"] is True
    _assert_catalog(doc)


def test_z9_spinel() -> None:
    """Honoring needs both endpoints registered, not only a standing commit."""
    doc = _reseat()
    svc = _by_name(doc)
    pairs = _by_pair(doc)
    standing = _standing_pairs()
    for pair in (("delta", "beta"), ("epsilon", "zeta"), ("zeta", "iota")):
        assert pair in standing
        assert pairs[pair]["honored"] is False
    assert svc["delta"]["registered"] is False
    assert svc["epsilon"]["registered"] is False
    assert svc["iota"]["registered"] is False
    assert pairs[("beta", "zeta")]["honored"] is True

    snap = _snapshot([FLOORS / "epsilon.floor", REPORT])
    try:
        (FLOORS / "epsilon.floor").write_text("3\n")
        doc2 = _reseat()
        assert doc2 == _expected_doc()
        svc2 = _by_name(doc2)
        pairs2 = _by_pair(doc2)
        assert svc2["epsilon"]["registered"] is True
        assert pairs2[("epsilon", "zeta")]["honored"] is True
        assert pairs2[("epsilon", "zeta")]["action"] == "deny"
        assert pairs2[("zeta", "iota")]["honored"] is False
        assert "epsilon=node-e7" in CATALOG.read_text().splitlines()
    finally:
        _restore(snap)
        _reseat()
