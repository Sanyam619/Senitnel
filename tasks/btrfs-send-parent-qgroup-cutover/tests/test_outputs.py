import json
import re
import subprocess
from pathlib import Path

ROOT = Path("/var/lib/btrfs")
ORIGINS = ROOT / "origins"
DECOYS = ROOT / "decoys"
SNAPS = ROOT / "snaps" / "payloads"
VOLUMES = ROOT / "volumes"
ATTACH = ROOT / "attach"
LEASES = Path("/var/run/btrfs")
OUT = Path("/output/lanes")
REPORT = Path("/output/send-report.json")
SEAL = Path("/etc/btrfs/pool.seal")
ROSTER = Path("/etc/btrfs/lane.roster")
WAL = ROOT / "journal" / "send.wal"
PARENTS = ROOT / "meta" / "parents.toml"
INTENT = ROOT / "meta" / "attach.intent"
CUT = "/app/ops/run_cutover.sh"
DESKD = "/app/ops/deskd"


def _digest(data: bytes) -> str:
    cp = subprocess.run(
        ["sha256sum"],
        input=data,
        capture_output=True,
        check=True,
    )
    return cp.stdout.decode().split()[0]


def _file_digest(path: Path) -> str:
    return _digest(path.read_bytes())


def _origin_digests() -> dict:
    return {p.name: _file_digest(p) for p in sorted(ORIGINS.glob("*.bin"))}


def _read_seal() -> int:
    for line in SEAL.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return int(line)
    raise AssertionError("empty seal")


def _roster() -> set[str]:
    names = set()
    for line in ROSTER.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            names.add(line)
    return names


def _expected_rows():
    cap = _read_seal()
    allow = _roster()
    latest = {}
    order = []
    seen = set()
    rows = []
    for line in WAL.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|")
        gen = int(parts[0])
        seq = int(parts[1])
        lane = parts[2]
        if gen > cap:
            continue
        if lane not in allow:
            continue
        rows.append((gen, seq, parts))
    rows.sort()
    for _gen, _seq, parts in rows:
        lane = parts[2]
        if lane not in seen:
            order.append(lane)
            seen.add(lane)
        latest[lane] = {
            "lane": lane,
            "parent": parts[3],
            "snap": parts[4],
            "origin": parts[5],
            "e": int(parts[6]),
            "f": int(parts[7]),
        }
    return [latest[d] for d in order]


def _parse_parents(text: str) -> dict[str, str]:
    tips = {}
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r'^([A-Za-z0-9_]+)\s*=\s*"([^"]*)"\s*$', line)
        if m:
            tips[m.group(1)] = m.group(2)
    return tips


def _expected_payload(row: dict) -> bytes:
    live = (ORIGINS / f"{row['origin']}.bin").read_bytes()
    cow = (SNAPS / f"{row['snap']}.bin").read_bytes()
    if row["e"] >= row["f"]:
        return cow
    return live


def _expected_kind(row: dict) -> str:
    return "incr" if row["e"] >= row["f"] else "base"


def _run_cut() -> subprocess.CompletedProcess:
    return subprocess.run(
        [CUT],
        check=False,
        capture_output=True,
        text=True,
    )


def _ensure_cutover() -> None:
    if not REPORT.exists() or not (OUT / "alpha" / "stream.bin").exists():
        cp = _run_cut()
        assert cp.returncode == 0, f"cutover failed: {cp.stderr}\n{cp.stdout}"


def test_k3_zircon():
    """Alpha stream follows sealed parent tip, not beyond-seal bogus."""
    rows = {r["lane"]: r for r in _expected_rows()}
    _ensure_cutover()
    got = (OUT / "alpha" / "stream.bin").read_bytes()
    assert got == _expected_payload(rows["alpha"])
    assert got != (SNAPS / "su-bogus.bin").read_bytes()
    assert got != (DECOYS / "d_alpha.bin").read_bytes()


def test_p2_garnet():
    """Gamma rejects decoy and below-floor incr tip."""
    rows = {r["lane"]: r for r in _expected_rows()}
    _ensure_cutover()
    got = (OUT / "gamma" / "stream.bin").read_bytes()
    assert got == _expected_payload(rows["gamma"])
    assert got == (ORIGINS / "o_gamma.bin").read_bytes()
    assert got != (DECOYS / "d_gamma.bin").read_bytes()
    assert got != (SNAPS / "su-gamma.bin").read_bytes()
    data = json.loads(REPORT.read_text())
    by_name = {d["name"]: d for d in data["lanes"]}
    assert by_name["gamma"]["origin_kind"] == "base"
    assert by_name["gamma"]["parent_uuid"] == rows["gamma"]["parent"]


def test_m8_obsidian():
    """Beta below floor materializes base origin bytes."""
    rows = {r["lane"]: r for r in _expected_rows()}
    _ensure_cutover()
    got = (OUT / "beta" / "stream.bin").read_bytes()
    assert got == _expected_payload(rows["beta"])
    assert got == (ORIGINS / "o_beta.bin").read_bytes()
    assert _expected_kind(rows["beta"]) == "base"
    data = json.loads(REPORT.read_text())
    by_name = {d["name"]: d for d in data["lanes"]}
    assert by_name["beta"]["origin_kind"] == "base"


def test_y3_coral():
    """Delta at epoch==floor is incr under equality-inclusive mode."""
    rows = {r["lane"]: r for r in _expected_rows()}
    _ensure_cutover()
    got = (OUT / "delta" / "stream.bin").read_bytes()
    assert got == _expected_payload(rows["delta"])
    assert got == (SNAPS / "su-delta.bin").read_bytes()
    data = json.loads(REPORT.read_text())
    by_name = {d["name"]: d for d in data["lanes"]}
    assert by_name["delta"]["origin_kind"] == "incr"


def test_q7_topaz():
    """Report parent_uuid, snap_uuid, origin_kind, order_index match sealed sequence."""
    rows = _expected_rows()
    by_exp = {r["lane"]: r for r in rows}
    _ensure_cutover()
    data = json.loads(REPORT.read_text())
    assert "lanes" in data
    by_name = {d["name"]: d for d in data["lanes"]}
    for lane, row in by_exp.items():
        assert lane in by_name
        assert by_name[lane]["parent_uuid"] == row["parent"]
        assert by_name[lane]["snap_uuid"] == row["snap"]
        assert by_name[lane]["origin_kind"] == _expected_kind(row)
    orders = [by_name[r["lane"]]["order_index"] for r in rows]
    assert orders == sorted(orders)
    assert len(set(orders)) == len(rows)
    assert set(by_name) == set(by_exp)


def test_r1_onyx():
    """Origins shelf digests stay unchanged without lease markers."""
    before = _origin_digests()
    _ensure_cutover()
    after = _origin_digests()
    assert before == after
    assert list(ORIGINS.glob("*.lease")) == []


def test_t6_amber():
    """Second cutover pass is byte-identical with clean leases."""
    _ensure_cutover()
    first = {
        p.name: _file_digest(p / "stream.bin") for p in OUT.iterdir() if p.is_dir()
    }
    cp = _run_cut()
    assert cp.returncode == 0, cp.stderr
    second = {
        p.name: _file_digest(p / "stream.bin") for p in OUT.iterdir() if p.is_dir()
    }
    assert first == second
    assert list(LEASES.glob("*.part")) == []
    assert list(ORIGINS.glob("*.lease")) == []


def test_v4_jade():
    """Concurrent cutover leaves clean leases and matching streams."""
    rows = {r["lane"]: r for r in _expected_rows()}
    _ensure_cutover()
    for p in LEASES.glob("*.part"):
        p.unlink()
    for p in ORIGINS.glob("*.lease"):
        p.unlink()
    script = (
        "import os,subprocess,sys\n"
        "p1=subprocess.Popen([sys.argv[1]])\n"
        "p2=subprocess.Popen([sys.argv[1]])\n"
        "sys.exit(0 if p1.wait()==0 and p2.wait()==0 else 1)\n"
    )
    cp = subprocess.run(
        ["python3", "-c", script, CUT],
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 0, cp.stderr
    assert list(LEASES.glob("*.part")) == []
    assert list(ORIGINS.glob("*.lease")) == []
    assert (OUT / "alpha" / "stream.bin").read_bytes() == _expected_payload(
        rows["alpha"]
    )
    assert (OUT / "gamma" / "stream.bin").read_bytes() == _expected_payload(
        rows["gamma"]
    )


def test_w9_quartz():
    """Stale parents.toml tips are rewritten from sealed roster parents."""
    rows = {r["lane"]: r for r in _expected_rows()}
    _ensure_cutover()
    PARENTS.write_text(
        '[parents]\nalpha = "pu-bogus"\nomega = "pu-omega"\n', encoding="utf-8"
    )
    runtime = ROOT / "meta" / "runtime.tsv"
    if runtime.exists():
        lines = []
        for line in runtime.read_text().splitlines():
            parts = line.split("\t")
            if len(parts) >= 3 and parts[1] == "alpha":
                parts[2] = "pu-bogus"
                lines.append("\t".join(parts))
            else:
                lines.append(line)
        runtime.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cp = _run_cut()
    assert cp.returncode == 0, cp.stderr
    assert (OUT / "alpha" / "stream.bin").read_bytes() == _expected_payload(
        rows["alpha"]
    )
    text = PARENTS.read_text(encoding="utf-8")
    assert "pu-bogus" not in text
    assert "omega" not in text
    tips = _parse_parents(text)
    for lane, row in rows.items():
        assert tips.get(lane) == row["parent"], f"{lane}: {tips.get(lane)} != {row['parent']}"
    assert set(tips) == set(rows)
    data = json.loads(REPORT.read_text())
    by_name = {d["name"]: d for d in data["lanes"]}
    assert by_name["alpha"]["parent_uuid"] == rows["alpha"]["parent"]


def test_x2_flint():
    """Surface OK does not replace correct incr-side lane payloads."""
    rows = {r["lane"]: r for r in _expected_rows()}
    _ensure_cutover()
    cp = subprocess.run(["/app/bin/healthb"], capture_output=True, text=True)
    assert cp.returncode == 0
    assert "OK" in cp.stdout
    for name in ("alpha", "delta"):
        got = (OUT / name / "stream.bin").read_bytes()
        assert got == _expected_payload(rows[name])
        assert got == (SNAPS / f"{rows[name]['snap']}.bin").read_bytes()
        assert got != (DECOYS / f"d_{name}.bin").read_bytes()
    data = json.loads(REPORT.read_text())
    by_name = {d["name"]: d for d in data["lanes"]}
    assert by_name["alpha"]["origin_kind"] == "incr"
    assert by_name["delta"]["origin_kind"] == "incr"


def test_n5_beryl():
    """Off-roster journal tips must not appear in lanes, report, or tip-map."""
    _ensure_cutover()
    assert not (OUT / "omega").exists()
    data = json.loads(REPORT.read_text())
    names = {d["name"] for d in data["lanes"]}
    assert "omega" not in names
    assert names == _roster()
    text = PARENTS.read_text(encoding="utf-8")
    assert "omega" not in text
    assert "pu-omega" not in text


def test_s4_jade():
    """Report seal_gen matches the active seal; attach intent is raw seal."""
    _ensure_cutover()
    data = json.loads(REPORT.read_text())
    assert data.get("seal_gen") == _read_seal()
    assert INTENT.read_text().strip() == "seal"


def test_i8_flint():
    """Attach points share inode with sealed shelf, not decoy copies."""
    _ensure_cutover()
    for lane in sorted(_roster()):
        sealed = VOLUMES / lane / "sealed" / "payload.bin"
        attached = ATTACH / f"{lane}.bin"
        assert sealed.exists() and attached.exists()
        assert not (ATTACH / lane / "payload.bin").exists()
        s1 = sealed.stat()
        s2 = attached.stat()
        assert s1.st_ino == s2.st_ino
        assert s1.st_dev == s2.st_dev
        decoy = VOLUMES / lane / "decoy" / "payload.bin"
        assert attached.read_bytes() != decoy.read_bytes()


def test_h2_coral():
    """Host markers under volumes/*/host/ are absent after cutover."""
    _ensure_cutover()
    for lane in sorted(_roster()):
        host = VOLUMES / lane / "host"
        if host.exists():
            assert list(host.iterdir()) == []
    assert list(LEASES.glob("*.part")) == []
    assert list(ORIGINS.glob("*.lease")) == []


def test_a1_desk():
    """Desk refresh must not clobber sealed hardlink identity."""
    _ensure_cutover()
    before = {
        lane: (ATTACH / f"{lane}.bin").stat().st_ino for lane in sorted(_roster())
    }
    cp = subprocess.run([DESKD], capture_output=True, text=True)
    assert cp.returncode == 0, cp.stderr
    for lane in sorted(_roster()):
        sealed = VOLUMES / lane / "sealed" / "payload.bin"
        attached = ATTACH / f"{lane}.bin"
        assert attached.stat().st_ino == sealed.stat().st_ino
        assert attached.stat().st_ino == before[lane]
        assert attached.read_bytes() != (VOLUMES / lane / "decoy" / "payload.bin").read_bytes()


def test_j2_journal():
    """Naive tip edit then cutover: crash rematerialize + sealed rewrite wins."""
    rows = {r["lane"]: r for r in _expected_rows()}
    _ensure_cutover()
    PARENTS.write_text(
        '[parents]\nalpha = "pu-hand"\nomega = "pu-omega"\n', encoding="utf-8"
    )
    INTENT.write_text("decoy\n")
    cp = _run_cut()
    assert cp.returncode == 0, cp.stderr
    assert INTENT.read_text().strip() == "seal"
    tips = _parse_parents(PARENTS.read_text())
    assert tips.get("alpha") == rows["alpha"]["parent"]
    assert "omega" not in tips
    assert "pu-hand" not in PARENTS.read_text()
