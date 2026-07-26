"""Verifier for lab Samba idmap cutover ops outcomes."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

REPORT = Path("/output/idmap-cutover.json")
ROSTER = Path("/etc/samba/idmap.roster")
SEAL = Path("/etc/samba/desk.seal")
TDB = Path("/var/lib/samba/idmap.tdb")
META = Path("/var/lib/samba/meta")
ACTIVE_KN = META / "active.kn"
GEN_LIVE = META / "gen.live"
GEN_TARGET = META / "gen.target"
CUT_ARM = META / "cut.arm"
CUT_OK = META / "cutover.ok"
PREF_ARMED = META / "pref.armed"
INTENT = META / "attach.intent"
BACKENDS = META / "backends.toml"
ATTACH = Path("/var/lib/samba/attach")
ORIGINS = Path("/var/lib/samba/origins")
VOLUMES = Path("/var/lib/samba/volumes")
RUN = Path("/var/run/samba")
FIXTURES = Path("/app/data/fixtures")
LEGACY_DROPIN = Path("/etc/samba/smb.conf.d/40-legacy.conf")
DESKD_ENV = Path("/etc/samba/deskd.env")


def _load_roster() -> list[dict]:
    rows = []
    for line in ROSTER.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        rows.append(
            {
                "name": parts[0],
                "sid": parts[1],
                "lo": int(parts[2]),
                "hi": int(parts[3]),
                "uid": int(parts[4]),
            }
        )
    return rows


def _bait() -> tuple[str, int]:
    for line in (FIXTURES / "principals.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("kind") == "bait":
            return str(row["sid"]), int(row["lo"])
    raise AssertionError("bait row missing from fixtures")


def _load_tdb() -> dict[str, tuple[int, int]]:
    out: dict[str, tuple[int, int]] = {}
    if not TDB.exists():
        return out
    for line in TDB.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        out[parts[0]] = (int(parts[1]), int(parts[2]))
    return out


def _load_report() -> dict:
    assert REPORT.exists(), "missing /output/idmap-cutover.json"
    return json.loads(REPORT.read_text())


def _sha256(path: Path) -> str:
    proc = subprocess.run(
        ["sha256sum", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.split()[0]


def _restore_stock_entrypoints() -> None:
    """Graders re-invoke stock seat/reload entrypoints (not agent-gutted copies)."""
    seed = Path("/app/samba-seed/ops")
    for name in ("run_idmapseat.sh", "run_reload.sh", "prep_s.sh"):
        src = seed / name
        dst = Path("/app/ops") / name
        if src.is_file():
            shutil.copy2(src, dst)
            os.chmod(dst, 0o755)


def _seat() -> None:
    _restore_stock_entrypoints()
    subprocess.run(["/app/ops/run_idmapseat.sh"], check=True)


def _reload() -> None:
    _restore_stock_entrypoints()
    subprocess.run(["/app/ops/run_reload.sh"], check=True)


def _ensure_materialized() -> None:
    if not REPORT.exists() or not TDB.exists() or not CUT_OK.exists():
        _seat()


def _env_kv() -> dict[str, str]:
    out = {}
    if not DESKD_ENV.exists():
        return out
    for line in DESKD_ENV.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _backend_kn() -> str:
    for line in BACKENDS.read_text().splitlines():
        line = line.strip()
        if line.startswith("kn="):
            return line.split("=", 1)[1].strip()
    raise AssertionError("backends.toml missing kn")


def test_report_schema():
    """Report has status ok plus backend, seal_gen, and principals rows."""
    _ensure_materialized()
    rep = _load_report()
    assert rep.get("status") == "ok"
    assert isinstance(rep.get("backend"), str) and rep["backend"]
    assert "seal_gen" in rep
    assert isinstance(rep.get("principals"), list)
    for row in rep["principals"]:
        for key in ("name", "sid", "uid", "gid", "range"):
            assert key in row


def test_seal_match():
    """seal_gen, cut.arm, and gen.live match desk.seal; intent is seal."""
    _ensure_materialized()
    rep = _load_report()
    seal = SEAL.read_text().strip()
    assert str(rep.get("seal_gen")).strip() == seal
    assert CUT_ARM.read_text().strip() == seal
    assert GEN_LIVE.read_text().strip() == seal
    assert CUT_OK.exists()
    assert INTENT.read_text().strip() == "seal"
    assert GEN_LIVE.read_text().strip() == GEN_TARGET.read_text().strip()


def test_roster_complete():
    """Every roster principal appears exactly once in the report."""
    _ensure_materialized()
    rep = _load_report()
    roster = _load_roster()
    names = [r["name"] for r in roster]
    got = [p["name"] for p in rep["principals"]]
    assert sorted(got) == sorted(names)
    assert len(got) == len(set(got))


def test_ranges_hold():
    """Exact roster uid/gid values hold and match wbinfo; backend is folded kn."""
    _ensure_materialized()
    rep = _load_report()
    roster = {r["name"]: r for r in _load_roster()}
    tdb = _load_tdb()
    kn = _backend_kn()
    for p in rep["principals"]:
        r = roster[p["name"]]
        assert int(p["uid"]) == r["uid"]
        assert int(p["gid"]) == r["uid"]
        assert r["lo"] <= int(p["uid"]) <= r["hi"]
        assert p["range"] == f"{r['lo']}-{r['hi']}"
        assert p["sid"] in tdb
        assert tdb[p["sid"]][0] == r["uid"]
        wb = subprocess.run(
            ["/app/bin/wbinfo", "-S", p["sid"]],
            check=True,
            capture_output=True,
            text=True,
        )
        assert int(wb.stdout.strip()) == r["uid"]
    assert rep.get("backend") == kn == ACTIVE_KN.read_text().strip()
    assert kn not in {"rid", "hash", "unset", ""}
    assert PREF_ARMED.exists()
    env = _env_kv()
    assert env.get("PAYLOAD_LINEAGE") == "sealed"


def test_decoy_absent():
    """Decoy sid/range must not appear in the report or live tdb mappings."""
    _ensure_materialized()
    rep = _load_report()
    tdb = _load_tdb()
    decoy_sid, decoy_lo = _bait()
    blob = json.dumps(rep)
    assert decoy_sid not in blob
    assert str(decoy_lo) not in blob
    assert decoy_sid not in tdb
    for p in rep["principals"]:
        assert int(p["uid"]) < decoy_lo


def test_tdb_agree():
    """Live idmap.tdb uids agree with the report for every principal."""
    _ensure_materialized()
    rep = _load_report()
    tdb = _load_tdb()
    for p in rep["principals"]:
        assert p["sid"] in tdb
        assert tdb[p["sid"]][0] == int(p["uid"])
        assert tdb[p["sid"]][1] == int(p["gid"])


def test_attach_hardlink():
    """Attach seats share inode with sealed shelves (flat .bin paths)."""
    _ensure_materialized()
    for r in _load_roster():
        dst = ATTACH / f"{r['name']}.bin"
        sealed = ORIGINS / r["name"] / "sealed" / "map.bin"
        assert dst.is_file()
        assert not (ATTACH / r["name"] / "map.bin").exists()
        assert os.stat(dst).st_ino == os.stat(sealed).st_ino


def test_host_scrub():
    """Host markers and torn leases are absent after successful cutover."""
    _ensure_materialized()
    host_files = list(VOLUMES.glob("*/host/*"))
    assert host_files == []
    leases = list(RUN.glob("lease.*"))
    assert leases == []


def test_seat_twice():
    """A second seat run leaves byte-identical report and tdb."""
    _ensure_materialized()
    before_report = REPORT.read_bytes()
    before_tdb = TDB.read_bytes()
    _seat()
    assert REPORT.read_bytes() == before_report
    assert TDB.read_bytes() == before_tdb


def test_reload_stable():
    """Reload must not restore legacy prefer hammer or churn seal/tdb."""
    _ensure_materialized()
    before_report = REPORT.read_bytes()
    before_tdb = TDB.read_bytes()
    before_seal = _load_report()["seal_gen"]
    _reload()
    after = _load_report()
    assert REPORT.read_bytes() == before_report
    assert TDB.read_bytes() == before_tdb
    assert str(after["seal_gen"]).strip() == str(before_seal).strip()
    assert ACTIVE_KN.read_text().strip() == _backend_kn()
    assert LEGACY_DROPIN.exists()
    hammer = Path("/var/lib/samba/journal/legacy.prefer").read_text()
    assert LEGACY_DROPIN.read_text() != hammer
    assert CUT_OK.exists()


def test_smblist_insufficient():
    """Share-list OK is not credit; idmap backend/ranges must still hold."""
    _ensure_materialized()
    sm = subprocess.run(["/app/bin/smblist"], check=True, capture_output=True, text=True)
    assert "labshare" in sm.stdout
    rep = _load_report()
    assert rep.get("backend") == _backend_kn()
    roster = {r["name"]: r for r in _load_roster()}
    assert len(rep["principals"]) == len(roster)
    for p in rep["principals"]:
        assert int(p["uid"]) == roster[p["name"]]["uid"]


def test_crash_tip_overwritten():
    """Crash backend map must not remain as the live folded backend."""
    _ensure_materialized()
    crash = (META / "backends.crash.toml").read_text()
    live = BACKENDS.read_text()
    assert live != crash
    assert "kn=hash" not in live
    tip_ok = (META / "tip.ok").read_text().strip()
    assert tip_ok == SEAL.read_text().strip()
    # Plaintext JSONL decoys must not be treated as the folded authority.
    assert (Path("/var/lib/samba/journal") / "tips.bin").is_file()
    assert (Path("/var/lib/samba/ops") / "journal.bin").is_file()


def test_reentry_after_clobber():
    """Clobbering live outputs and reseating restores correct end-state."""
    _ensure_materialized()
    REPORT.write_text("{}\n")
    TDB.write_text("")
    CUT_OK.unlink(missing_ok=True)
    GEN_LIVE.unlink(missing_ok=True)
    _seat()
    rep = _load_report()
    assert rep["status"] == "ok"
    assert rep["backend"] == _backend_kn()
    assert str(rep["seal_gen"]).strip() == SEAL.read_text().strip()
    roster = {r["name"]: r for r in _load_roster()}
    assert len(rep["principals"]) == len(roster)
    for p in rep["principals"]:
        assert int(p["uid"]) == roster[p["name"]]["uid"]
    for r in _load_roster():
        assert os.stat(ATTACH / f"{r['name']}.bin").st_ino == os.stat(
            ORIGINS / r["name"] / "sealed" / "map.bin"
        ).st_ino


def test_fixtures_frozen():
    """Fixture seed bytes under /app/data/fixtures remain unchanged."""
    anchor = (FIXTURES / "anchor.sha256").read_text().strip().split()
    assert len(anchor) >= 1
    expected = anchor[0]
    actual = _sha256(FIXTURES / "principals.jsonl")
    assert actual == expected
