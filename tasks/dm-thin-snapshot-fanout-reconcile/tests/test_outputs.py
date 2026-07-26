import json
import os
import re
import subprocess
from pathlib import Path

POOL = Path("/var/lib/pool")
ORIGINS = POOL / "origins"
DECOYS = POOL / "decoys"
SNAPS = POOL / "snaps" / "payloads"
LEASES = Path("/var/run/pool")
OUT = Path("/output/drills")
REPORT = Path("/output/fanout-report.json")
SEAL = Path("/etc/pool/pool.seal")
ROSTER = Path("/etc/pool/drill.roster")
WAL = POOL / "journal" / "act.wal"
ACTIVATION = POOL / "meta" / "activation.toml"
MAT = "/app/ops/run_materialize.sh"


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
        drill = parts[2]
        if gen > cap:
            continue
        if drill not in allow:
            continue
        rows.append((gen, seq, parts))
    rows.sort()
    for _gen, _seq, parts in rows:
        drill = parts[2]
        if drill not in seen:
            order.append(drill)
            seen.add(drill)
        latest[drill] = {
            "drill": drill,
            "tip": parts[3],
            "origin": parts[4],
            "e": int(parts[6]),
            "f": int(parts[7]),
        }
    return [latest[d] for d in order]


def _parse_activation_tips(text: str) -> dict[str, str]:
    tips = {}
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r'^([A-Za-z0-9_]+)\s*=\s*"([^"]*)"\s*$', line)
        if m:
            tips[m.group(1)] = m.group(2)
    return tips


def _expected_payload(row: dict) -> bytes:
    live = (ORIGINS / f"{row['origin']}.bin").read_bytes()
    cow = (SNAPS / f"{row['tip']}.bin").read_bytes()
    if row["e"] >= row["f"]:
        return cow
    return live


def _expected_kind(row: dict) -> str:
    return "cow" if row["e"] >= row["f"] else "live"


def _run_matfan() -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "/app/lib"
    return subprocess.run(
        [MAT],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def _ensure_materialized() -> None:
    if not REPORT.exists() or not (OUT / "alpha" / "payload.bin").exists():
        cp = _run_matfan()
        assert cp.returncode == 0, f"matfan failed: {cp.stderr}\n{cp.stdout}"


def test_k3_zircon():
    """Alpha payload follows sealed tip, not beyond-seal bogus tip."""
    rows = {r["drill"]: r for r in _expected_rows()}
    _ensure_materialized()
    got = (OUT / "alpha" / "payload.bin").read_bytes()
    assert got == _expected_payload(rows["alpha"])
    assert got != (SNAPS / "t_bogus.bin").read_bytes()


def test_p2_garnet():
    """Gamma rejects stamp-matching decoy and below-floor cow tip."""
    rows = {r["drill"]: r for r in _expected_rows()}
    _ensure_materialized()
    got = (OUT / "gamma" / "payload.bin").read_bytes()
    assert got == _expected_payload(rows["gamma"])
    assert got == (ORIGINS / "o_gamma.bin").read_bytes()
    assert got != (DECOYS / "d_gamma.bin").read_bytes()
    assert got != (SNAPS / "t_gamma.bin").read_bytes()
    data = json.loads(REPORT.read_text())
    by_name = {d["name"]: d for d in data["drills"]}
    assert by_name["gamma"]["origin_kind"] == "live"
    assert by_name["gamma"]["tip_id"] == rows["gamma"]["tip"]


def test_m8_obsidian():
    """Beta below floor materializes live origin bytes."""
    rows = {r["drill"]: r for r in _expected_rows()}
    _ensure_materialized()
    got = (OUT / "beta" / "payload.bin").read_bytes()
    assert got == _expected_payload(rows["beta"])
    assert got == (ORIGINS / "o_beta.bin").read_bytes()
    assert _expected_kind(rows["beta"]) == "live"
    data = json.loads(REPORT.read_text())
    by_name = {d["name"]: d for d in data["drills"]}
    assert by_name["beta"]["origin_kind"] == "live"


def test_q7_topaz():
    """Report tip_id, origin_kind, and order_index match sealed sequence."""
    rows = _expected_rows()
    by_exp = {r["drill"]: r for r in rows}
    _ensure_materialized()
    data = json.loads(REPORT.read_text())
    assert "drills" in data
    by_name = {d["name"]: d for d in data["drills"]}
    for drill, row in by_exp.items():
        assert drill in by_name
        assert by_name[drill]["tip_id"] == row["tip"]
        assert by_name[drill]["origin_kind"] == _expected_kind(row)
    orders = [by_name[r["drill"]]["order_index"] for r in rows]
    assert orders == sorted(orders)
    assert len(set(orders)) == len(rows)
    assert set(by_name) == set(by_exp)


def test_r1_onyx():
    """Origins shelf digests stay unchanged without lease markers."""
    before = _origin_digests()
    _ensure_materialized()
    after = _origin_digests()
    assert before == after
    assert list(ORIGINS.glob("*.lease")) == []


def test_t6_amber():
    """Second materialize pass is byte-identical with clean leases."""
    _ensure_materialized()
    first = {
        p.name: _file_digest(p / "payload.bin") for p in OUT.iterdir() if p.is_dir()
    }
    cp = _run_matfan()
    assert cp.returncode == 0, cp.stderr
    second = {
        p.name: _file_digest(p / "payload.bin") for p in OUT.iterdir() if p.is_dir()
    }
    assert first == second
    assert list(LEASES.glob("*.part")) == []
    assert list(ORIGINS.glob("*.lease")) == []


def test_v4_jade():
    """Concurrent materialize leaves clean leases and matching payloads."""
    rows = {r["drill"]: r for r in _expected_rows()}
    _ensure_materialized()
    for p in LEASES.glob("*.part"):
        p.unlink()
    for p in ORIGINS.glob("*.lease"):
        p.unlink()
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "/app/lib"
    script = (
        "import os,subprocess,sys\n"
        "env=os.environ.copy()\n"
        "p1=subprocess.Popen([sys.argv[1]],env=env)\n"
        "p2=subprocess.Popen([sys.argv[1]],env=env)\n"
        "sys.exit(0 if p1.wait()==0 and p2.wait()==0 else 1)\n"
    )
    cp = subprocess.run(
        ["python3", "-c", script, MAT],
        env=env,
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 0, cp.stderr
    assert list(LEASES.glob("*.part")) == []
    assert list(ORIGINS.glob("*.lease")) == []
    assert (OUT / "alpha" / "payload.bin").read_bytes() == _expected_payload(
        rows["alpha"]
    )
    assert (OUT / "gamma" / "payload.bin").read_bytes() == _expected_payload(
        rows["gamma"]
    )
    assert (OUT / "beta" / "payload.bin").read_bytes() == _expected_payload(
        rows["beta"]
    )


def test_w9_quartz():
    """Stale activation tips are rewritten from sealed roster tips."""
    rows = {r["drill"]: r for r in _expected_rows()}
    _ensure_materialized()
    ACTIVATION.write_text(
        '[tips]\nalpha = "t_bogus"\nomega = "t_omega"\n', encoding="utf-8"
    )
    runtime = POOL / "meta" / "runtime.tsv"
    if runtime.exists():
        lines = []
        for line in runtime.read_text().splitlines():
            parts = line.split("\t")
            if len(parts) >= 3 and parts[1] == "alpha":
                parts[2] = "t_bogus"
                lines.append("\t".join(parts))
            else:
                lines.append(line)
        runtime.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cp = _run_matfan()
    assert cp.returncode == 0, cp.stderr
    assert (OUT / "alpha" / "payload.bin").read_bytes() == _expected_payload(
        rows["alpha"]
    )
    text = ACTIVATION.read_text(encoding="utf-8")
    assert "t_bogus" not in text
    assert "omega" not in text
    tips = _parse_activation_tips(text)
    for drill, row in rows.items():
        assert tips.get(drill) == row["tip"], f"{drill}: {tips.get(drill)} != {row['tip']}"
    assert set(tips) == set(rows)
    data = json.loads(REPORT.read_text())
    by_name = {d["name"]: d for d in data["drills"]}
    assert by_name["alpha"]["tip_id"] == rows["alpha"]["tip"]


def test_x2_flint():
    """Surface OK does not replace correct cow-side drill payloads."""
    rows = {r["drill"]: r for r in _expected_rows()}
    _ensure_materialized()
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "/app/lib"
    cp = subprocess.run(
        ["/app/bin/dmhealth"], capture_output=True, text=True, env=env
    )
    assert cp.returncode == 0
    assert "OK" in cp.stdout
    for name in ("alpha", "delta"):
        got = (OUT / name / "payload.bin").read_bytes()
        assert got == _expected_payload(rows[name])
        assert got == (SNAPS / f"{rows[name]['tip']}.bin").read_bytes()
    data = json.loads(REPORT.read_text())
    by_name = {d["name"]: d for d in data["drills"]}
    assert by_name["alpha"]["origin_kind"] == "cow"
    assert by_name["delta"]["origin_kind"] == "cow"


def test_n5_beryl():
    """Off-roster journal tips must not fan out into drills or the report."""
    _ensure_materialized()
    assert not (OUT / "omega").exists()
    data = json.loads(REPORT.read_text())
    names = {d["name"] for d in data["drills"]}
    assert "omega" not in names
    assert names == _roster()
    text = ACTIVATION.read_text(encoding="utf-8")
    assert "omega" not in text
    assert "t_omega" not in text


def test_y3_coral():
    """Report seal_gen matches the active seal and roster tip map."""
    rows = _expected_rows()
    _ensure_materialized()
    data = json.loads(REPORT.read_text())
    assert data.get("seal_gen") == _read_seal()
    by_name = {d["name"]: d for d in data["drills"]}
    assert set(by_name) == {r["drill"] for r in rows}
    for row in rows:
        assert by_name[row["drill"]]["tip_id"] == row["tip"]
