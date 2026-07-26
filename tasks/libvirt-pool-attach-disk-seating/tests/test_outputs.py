import json
import re
import subprocess
from pathlib import Path

ENTRY = "/app/ops/run_pool_attach.sh"
BINARY = "/app/bin/virtattach"
REPORT = Path("/output/libvirt-attach.json")

QEMU_DIR = Path("/etc/libvirt/qemu")
STORAGE_DIR = Path("/etc/libvirt/storage")
OPS_DIR = Path("/var/lib/libvirt/ops")
STATE_ROOT = Path("/var/lib/libvirt/storage")
LEASE_DIR = Path("/var/run/libvirt")
ATTACH_D = QEMU_DIR / "attach.d"
ROSTER = QEMU_DIR / "seat.roster"
SEAL = STORAGE_DIR / "attach.seal"
JOURNAL = OPS_DIR / "cutover.journal"

DATA_POOLS = Path("/app/data/pools")


def _run(cmd):
    return subprocess.run(cmd, check=False, capture_output=True, text=True)


def _run_entrypoint():
    return _run(["bash", ENTRY])


def _ensure_reconciled():
    if not REPORT.exists():
        _run_entrypoint()


def _report():
    _ensure_reconciled()
    return json.loads(REPORT.read_text())


def _roster():
    rows = []
    for line in ROSTER.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = line.split("|")
        if len(p) < 4:
            continue
        rows.append({"domain": p[0], "target": p[1], "pool": p[2], "volume": p[3]})
    return rows


def _seal_cap():
    for line in SEAL.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        return int(line)
    return 0


def _durable():
    """Latest per-roster-pool identity from the journal, capped by the seal."""
    cap = _seal_cap()
    pools = {r["pool"] for r in _roster()}
    best = {}
    for line in JOURNAL.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = line.split("|")
        if len(p) < 5:
            continue
        gen, seq, pool, uuid, path = int(p[0]), int(p[1]), p[2], p[3], p[4]
        if pool not in pools or gen > cap:
            continue
        rank = gen * 100000 + seq
        if pool not in best or rank > best[pool][0]:
            best[pool] = (rank, uuid, path)
    return {k: (v[1], v[2]) for k, v in best.items()}


def _surface(pool):
    xml = (STORAGE_DIR / f"pool_{pool}.xml").read_text()
    u = re.search(r"<uuid>\s*([^<]+?)\s*</uuid>", xml)
    p = re.search(r"(?s)<target>.*?<path>\s*([^<]+?)\s*</path>", xml)
    return (u.group(1).strip() if u else "", p.group(1).strip() if p else "")


def _dom_source_uuid(domain, target):
    xml = (QEMU_DIR / f"dom_{domain}.xml").read_text()
    blocks = re.findall(r"(?s)<disk\b.*?</disk>", xml)
    for b in blocks:
        if f"dev='{target}'" in b:
            m = re.search(r"<source\b[^>]*\buuid='([^']*)'", b)
            if m:
                return m.group(1)
    return ""


def _capped_gen_counts():
    """Per-roster-pool count of journal generations within the seal cap."""
    cap = _seal_cap()
    pools = {r["pool"] for r in _roster()}
    counts = {}
    for line in JOURNAL.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = line.split("|")
        if len(p) < 5:
            continue
        gen, pool = int(p[0]), p[2]
        if pool in pools and gen <= cap:
            counts[pool] = counts.get(pool, 0) + 1
    return counts


def test_j4_slate_first_roster_disk_bound_to_durable_identity():
    """The first roster disk's reported identity and its domain binding follow
    the durable authority, not the drifted surface pool definition."""
    data = _report()
    row = _roster()[0]
    dur_uuid, dur_path = _durable()[row["pool"]]
    surf_uuid, _ = _surface(row["pool"])
    pool = next(p for p in data["pools"] if p["name"] == row["pool"])
    assert pool["uuid"] == dur_uuid
    assert pool["path"] == dur_path
    assert pool["uuid"] != surf_uuid
    assert _dom_source_uuid(row["domain"], row["target"]) == dur_uuid


def test_p8_quartz_superseded_generation_pool_uses_latest():
    """A pool with multiple in-cap journal generations resolves to the newest,
    discarding both the surface decoy and older superseded generations."""
    data = _report()
    counts = _capped_gen_counts()
    by_pool = {r["pool"]: r for r in _roster()}
    candidates = [p for p in by_pool if counts.get(p, 0) > 1]
    assert candidates, "expected a pool with >1 in-cap generation"
    name = candidates[-1]
    row = by_pool[name]
    dur_uuid, dur_path = _durable()[name]
    surf_uuid, _ = _surface(name)
    pool = next(p for p in data["pools"] if p["name"] == name)
    assert pool["uuid"] == dur_uuid
    assert pool["path"] == dur_path
    assert pool["uuid"] != surf_uuid
    assert _dom_source_uuid(row["domain"], row["target"]) == dur_uuid


def test_k9_marl_every_pool_active():
    """Every in-scope pool is reported active after reconciliation."""
    data = _report()
    assert len(data["pools"]) == len({r["pool"] for r in _roster()})
    for p in data["pools"]:
        assert p["state"] == "active", p


def test_c3_ochre_receipts_are_key_value_not_json():
    """Cutover receipts are written as key=value under the durable identity;
    JSON-shaped receipts are not accepted as authorization."""
    _ensure_reconciled()
    dur = _durable()
    for r in _roster():
        rc = OPS_DIR / "receipts" / f"{r['domain']}-{r['target']}.receipt"
        assert rc.exists(), rc
        text = rc.read_text()
        assert not text.lstrip().startswith("{"), f"JSON receipt not accepted: {rc}"
        kv = {}
        for line in text.splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                kv[k.strip()] = v.strip()
        assert kv.get("pool") == r["pool"]
        assert kv.get("uuid") == dur[r["pool"]][0]


def test_r5_flint_all_disks_attached_with_durable_sources():
    """attach_ok is true only when every roster disk is attached with a source
    path rooted at its pool's durable target path."""
    data = _report()
    dur = _durable()
    assert data["attach_ok"]
    seen = set()
    for d in data["disks"]:
        seen.add((d["domain"], d["target"]))
        assert d["attached"], d
        _, dur_path = dur[d["pool"]]
        assert d["source"] == f"{dur_path}/{r_vol(d['domain'], d['target'])}"
    assert seen == {(r["domain"], r["target"]) for r in _roster()}


def r_vol(domain, target):
    for r in _roster():
        if r["domain"] == domain and r["target"] == target:
            return r["volume"]
    return ""


def test_w2_onyx_naive_domain_edit_is_rematerialized():
    """A hand-edited domain source is rematerialized to the durable identity on
    the next entrypoint run, and the disk still attaches."""
    _ensure_reconciled()
    row = _roster()[0]
    dur_uuid, _ = _durable()[row["pool"]]
    dom = QEMU_DIR / f"dom_{row['domain']}.xml"
    original = dom.read_text()
    # Derive a bogus binding from the durable one (no hardcoded oracle value).
    bogus = dur_uuid[:-2] + ("00" if not dur_uuid.endswith("00") else "11")
    try:
        tampered = re.sub(
            r"(<source\b[^>]*\buuid=')[^']*(')",
            r"\g<1>" + bogus + r"\g<2>",
            original,
            count=1,
        )
        dom.write_text(tampered)
        assert _dom_source_uuid(row["domain"], row["target"]) != dur_uuid
        _run_entrypoint()
        assert _dom_source_uuid(row["domain"], row["target"]) == dur_uuid
        data = json.loads(REPORT.read_text())
        disk = next(d for d in data["disks"] if d["domain"] == row["domain"])
        assert disk["attached"]
    finally:
        if _dom_source_uuid(row["domain"], row["target"]) != dur_uuid:
            dom.write_text(original)
            _run_entrypoint()


def test_m6_verd_surface_selection_reverts_to_decoy():
    """When selection prefers the surface authority, the engine rebinds to the
    surface decoy and attach_ok goes false: the override is load-bearing."""
    _ensure_reconciled()
    row = _roster()[0]
    surf_uuid, _ = _surface(row["pool"])
    select = ATTACH_D / "10-select.conf"
    saved = select.read_text()
    try:
        select.write_text("authority=surface\n")
        # Invoke the sealed engine directly, bypassing the ops staging helpers.
        _run([BINARY])
        data = json.loads(REPORT.read_text())
        assert not data["attach_ok"]
        assert _dom_source_uuid(row["domain"], row["target"]) == surf_uuid
    finally:
        select.write_text(saved)
        _run_entrypoint()


def test_t7_umber_torn_lease_markers_cleaned():
    """Torn lease markers left by the crash are cleared after reconciliation."""
    _ensure_reconciled()
    leftovers = list(LEASE_DIR.glob("*.part")) + list(LEASE_DIR.glob("*.lock"))
    assert leftovers == [], leftovers


def test_d1_slate2_report_is_idempotent():
    """Two consecutive entrypoint runs produce a byte-identical report."""
    _ensure_reconciled()
    _run_entrypoint()
    first = REPORT.read_bytes()
    _run_entrypoint()
    second = REPORT.read_bytes()
    assert first == second


def test_x9_scope_off_roster_pools_and_domains_excluded():
    """Only roster pools/domains appear; off-roster definitions are untouched
    and get no receipt."""
    data = _report()
    roster_pools = {r["pool"] for r in _roster()}
    roster_doms = {r["domain"] for r in _roster()}
    assert {p["name"] for p in data["pools"]} == roster_pools
    assert {d["domain"] for d in data["disks"]} == roster_doms
    assert "omega" not in {p["name"] for p in data["pools"]}
    # An off-roster domain definition must be left untouched.
    ghost = _dom_source_uuid("ghost", "vda")
    surf_omega, _ = _surface("omega")
    assert ghost == surf_omega
    assert not (OPS_DIR / "receipts" / "ghost-vda.receipt").exists()


def test_f0_frozen_volume_fixtures_unchanged():
    """The volume seed fixtures under /app/data/pools stay byte-for-byte across
    a reconcile pass."""
    before = {p.name: p.read_bytes() for p in sorted(DATA_POOLS.glob("*.img"))}
    assert before, "no volume fixtures found"
    _run_entrypoint()
    for name, content in before.items():
        assert (DATA_POOLS / name).read_bytes() == content, f"{name} was modified"


def test_h5_bait_surface_health_is_not_the_attach_signal():
    """virthealth can print a healthy line even when seating is real; the
    report, not the health probe, is the source of truth for attachment."""
    res = _run(["/usr/local/bin/virthealth"])
    assert res.returncode == 0
    assert "status=OK" in res.stdout
    # Health is green, but real seating is only proven by the report.
    data = _report()
    assert data["attach_ok"]
    assert all(d["attached"] for d in data["disks"])
