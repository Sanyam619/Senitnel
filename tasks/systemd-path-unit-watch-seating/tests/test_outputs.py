"""Verifier for systemd path-unit watch seating."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

REPORT = Path("/output/path-seat.json")
META_D = Path("/app/data/pathunits")
EXTRA_D = Path("/var/lib/systemd/ops/extra")
PIN = Path("/app/packaging/pathunits.sha256")
SITE = Path("/app/config/site_standard.conf")
ETC = Path("/etc/systemd/system")
OPS = Path("/var/lib/systemd/ops")
ABORT = OPS / "abort.d" / "deploy-artifact.path.d" / "90-local.conf"
LIVE_DROP = ETC / "deploy-artifact.path.d" / "90-local.conf"
ARMED_MAP = Path("/run/systemd/watch-seat/armed.map")
LOADED_MAP = Path("/run/systemd/watch-seat/loaded.map")
RECEIPT = OPS / "state" / "cutover.ok"
GEN_TARGET = OPS / "state" / "generation.target"
GEN_LIVE = OPS / "state" / "generation.live"
PREFER = OPS / "prefer.jsonl"
TRIG = OPS / "triggers.jsonl"
LIVE = OPS / "live"
PATHSEAT = Path("/app/publisher/pathseat")


def _run(cmd: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def _reseat() -> dict:
    REPORT.unlink(missing_ok=True)
    proc = _run(["/bin/bash", "/app/ops/run_path_seat.sh"], check=False)
    assert proc.returncode == 0, f"seat failed: {proc.stderr}\n{proc.stdout}"
    assert REPORT.is_file(), "missing /output/path-seat.json"
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


def _read_int(p: Path) -> int:
    return int(p.read_text().strip()) if p.exists() else 0


def _load_units() -> dict[str, dict[str, str]]:
    units: dict[str, dict[str, str]] = {}
    roots = [META_D]
    if EXTRA_D.is_dir():
        roots.append(EXTRA_D)
    for root in roots:
        for m in sorted(root.glob("*.meta")):
            kv = _parse_kv(m.read_text())
            if "id" in kv:
                units[kv["id"]] = kv
    return units


def _fold_unit(unit: str) -> tuple[str, str, str]:
    exists = ""
    changed = ""
    dne = ""
    section = ""
    files: list[Path] = []
    base = ETC / f"{unit}.path"
    if base.exists():
        files.append(base)
    dd = ETC / f"{unit}.path.d"
    if dd.is_dir():
        files.extend(sorted(dd.glob("*.conf")))
    for f in files:
        for line in f.read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                section = line
                continue
            if section != "[Path]" or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()
            if k == "PathExists":
                exists = v
            elif k == "PathChanged":
                changed = v
            elif k == "DirectoryNotEmpty":
                dne = v
    return exists, changed, dne


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


def _active_triggers() -> dict[str, int]:
    fire: dict[str, tuple[str, int]] = {}
    for line in TRIG.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("kind") == "fire":
            fire[row["eid"]] = (row["unit"], int(row["epoch"]))
        elif row.get("kind") == "retract":
            fire.pop(row.get("eid"), None)
    last: dict[str, int] = {}
    for unit, epoch in fire.values():
        if unit not in last or epoch > last[unit]:
            last[unit] = epoch
    return last


def _finite_int(v: object) -> bool:
    return isinstance(v, int) and float("-inf") < float(v) < float("inf")


def _expected_doc() -> tuple[dict, dict[str, str]]:
    units = _load_units()
    batch = _pick_batch()
    tips = {r["id"]: int(r["tip"]) for r in batch["rows"]}
    exp_ex = {r["id"]: r.get("exists", "") for r in batch["rows"]}
    exp_ch = {r["id"]: r.get("changed", "") for r in batch["rows"]}
    last = _active_triggers()

    paths = []
    armed_map: dict[str, str] = {}
    armed_of: dict[str, bool] = {}
    for unit in sorted(units):
        fe, fc, fd = _fold_unit(unit)
        floor = _read_int(OPS / "floors" / f"{unit}.floor")
        wg = _read_int(OPS / "watchgen" / f"{unit}.gen")
        tip = tips.get(unit, 0)
        armed = (
            fe == exp_ex.get(unit, "")
            and fc == exp_ch.get(unit, "")
            and tip >= floor
            and wg >= floor
            and fd == ""
        )
        armed_of[unit] = armed
        paths.append(
            {
                "unit": unit,
                "path_exists": fe,
                "path_changed": fc,
                "generation": tip,
                "armed": armed,
            }
        )
        if armed:
            armed_map[unit] = fe

    triggers = []
    for unit in sorted(last):
        triggers.append(
            {
                "unit": unit,
                "last_epoch": last[unit],
                "honored": bool(armed_of.get(unit, False)),
            }
        )

    doc = {
        "schema_tag": "path-seat-v1",
        "paths": paths,
        "triggers": triggers,
        "seat_ok": True,
    }
    return doc, armed_map


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


def _assert_armed_map(doc: dict) -> None:
    assert ARMED_MAP.is_file()
    expected = {p["path_exists"]: p["unit"] for p in doc["paths"] if p["armed"]}
    # armed.map is unit=path lines; invert to path->unit for comparison stability
    got_kv = _parse_kv(ARMED_MAP.read_text())
    got = {v: k for k, v in got_kv.items()}
    assert got == expected


def test_q3_topaz() -> None:
    """Baseline schema types, full ledger equality, armed.map, and seat_ok."""
    doc = _reseat()
    exp, _ = _expected_doc()
    assert doc["schema_tag"] == "path-seat-v1"
    assert isinstance(doc["paths"], list)
    assert isinstance(doc["triggers"], list)
    assert isinstance(doc["seat_ok"], bool)
    assert doc["seat_ok"] is True
    needed = {"unit", "path_exists", "path_changed", "generation", "armed"}
    for row in doc["paths"]:
        assert needed <= set(row)
        assert isinstance(row["unit"], str)
        assert isinstance(row["path_exists"], str)
        assert isinstance(row["path_changed"], str)
        assert _finite_int(row["generation"])
        assert isinstance(row["armed"], bool)
    for row in doc["triggers"]:
        assert {"unit", "last_epoch", "honored"} <= set(row)
        assert isinstance(row["unit"], str)
        assert _finite_int(row["last_epoch"])
        assert isinstance(row["honored"], bool)
    assert doc["paths"] == exp["paths"]
    assert doc["triggers"] == exp["triggers"]
    _assert_armed_map(doc)


def test_n4_beryl() -> None:
    """Two seating passes leave byte-identical output and a stable live generation."""
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


def test_v5_coral() -> None:
    """Latest sealed and complete batch wins over the unsealed later batch."""
    doc = _reseat()
    batch = _pick_batch()
    assert int(batch["gen"]) == 7
    assert batch.get("sealed") is True
    assert batch.get("complete") is True
    by_unit = {p["unit"]: p for p in doc["paths"]}
    assert by_unit["deploy-artifact"]["generation"] == 7
    assert by_unit["spool-flush"]["generation"] == 2
    assert GEN_LIVE.read_text().strip() == "7"
    for p in doc["paths"]:
        assert p["generation"] != 99


def test_w7_quartz() -> None:
    """Frozen fixtures and prebuilt publisher stay pinned; a novel extra unit seats."""
    assert PIN.is_file()
    meta_digests: dict[str, str] = {}
    seat_digest = None
    for line in PIN.read_text().splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        digest, path = line.split(None, 1)
        path = path.strip()
        if path.endswith("pathseat"):
            seat_digest = digest
        else:
            meta_digests[Path(path).name] = digest
    assert seat_digest is not None
    assert seat_digest == _file_sha256(PATHSEAT)
    assert meta_digests
    for name, digest in meta_digests.items():
        assert _file_sha256(META_D / name) == digest

    mirror_pe = "/srv/m/in"
    paths = [
        PREFER,
        ETC / "mirror-sync.path",
        EXTRA_D / "mirror-sync.meta",
        OPS / "floors" / "mirror-sync.floor",
        OPS / "watchgen" / "mirror-sync.gen",
        REPORT,
    ]
    snap = _snapshot_paths(paths)
    try:
        EXTRA_D.mkdir(parents=True, exist_ok=True)
        (EXTRA_D / "mirror-sync.meta").write_text(
            "id=mirror-sync\nservice=mirror-sync.service\nbase=/srv/m\n"
        )
        (ETC / "mirror-sync.path").write_text(
            f"[Path]\nPathExists={mirror_pe}\n"
        )
        (OPS / "floors" / "mirror-sync.floor").write_text("1\n")
        (OPS / "watchgen" / "mirror-sync.gen").write_text("7\n")
        batch = _pick_batch()
        rows = list(batch["rows"]) + [
            {"id": "mirror-sync", "exists": mirror_pe, "changed": "", "tip": 7}
        ]
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
        by_unit = {p["unit"]: p for p in doc["paths"]}
        assert "mirror-sync" in by_unit
        assert by_unit["mirror-sync"]["armed"] is True
        assert by_unit["mirror-sync"]["path_exists"] == mirror_pe
        assert by_unit["mirror-sync"]["generation"] == 7
        _assert_armed_map(doc)
        for name, digest in meta_digests.items():
            assert _file_sha256(META_D / name) == digest
        assert _file_sha256(PATHSEAT) == seat_digest
    finally:
        _restore_paths(snap)
        if EXTRA_D.exists():
            shutil.rmtree(EXTRA_D)
        _reseat()


def test_p9_jade() -> None:
    """DirectoryNotEmpty bait: matching PathExists is not enough to arm."""
    doc = _reseat()
    exp, _ = _expected_doc()
    by_unit = {p["unit"]: p for p in doc["paths"]}
    by_exp = {p["unit"]: p for p in exp["paths"]}
    assert by_unit["config-reload"]["path_exists"] == by_exp["config-reload"]["path_exists"]
    assert by_unit["config-reload"]["armed"] is False
    assert "config-reload" not in _parse_kv(ARMED_MAP.read_text())

    dropin = ETC / "config-reload.path.d" / "70-nodne.conf"
    snap = _snapshot_paths([dropin, REPORT])
    try:
        dropin.parent.mkdir(parents=True, exist_ok=True)
        dropin.write_text("[Path]\nDirectoryNotEmpty=\n")
        doc2 = _reseat()
        by2 = {p["unit"]: p for p in doc2["paths"]}
        assert by2["config-reload"]["armed"] is True
    finally:
        _restore_paths(snap)
        if dropin.exists() and snap.get(str(dropin)) is None:
            dropin.unlink()
        _reseat()


def test_r6_slate() -> None:
    """Generation floor keeps a below-floor unit unarmed; others arm independently."""
    doc = _reseat()
    by_unit = {p["unit"]: p for p in doc["paths"]}
    assert by_unit["spool-flush"]["generation"] == 2
    assert by_unit["spool-flush"]["armed"] is False
    assert by_unit["deploy-artifact"]["armed"] is True
    assert by_unit["cert-bundle"]["armed"] is True
    assert by_unit["log-rotate"]["armed"] is True
    assert doc["seat_ok"] is True
    _assert_armed_map(doc)


def test_y2_onyx() -> None:
    """Watch generation below floor keeps a matching unit unarmed until raised."""
    doc = _reseat()
    exp, _ = _expected_doc()
    by_unit = {p["unit"]: p for p in doc["paths"]}
    by_exp = {p["unit"]: p for p in exp["paths"]}
    assert by_unit["cache-prime"]["path_exists"] == by_exp["cache-prime"]["path_exists"]
    assert by_unit["cache-prime"]["generation"] == by_exp["cache-prime"]["generation"]
    assert by_unit["cache-prime"]["armed"] is False

    wg = OPS / "watchgen" / "cache-prime.gen"
    snap = _snapshot_paths([wg, REPORT])
    try:
        wg.write_text("9\n")
        doc2 = _reseat()
        by2 = {p["unit"]: p for p in doc2["paths"]}
        assert by2["cache-prime"]["armed"] is True
        assert by2["cache-prime"]["unit"] in _parse_kv(ARMED_MAP.read_text())
    finally:
        _restore_paths(snap)
        _reseat()


def test_b6_cobalt() -> None:
    """Lexical drop-in fold resolves the watched path; a later drop-in overrides it."""
    doc = _reseat()
    exp, _ = _expected_doc()
    by_unit = {p["unit"]: p for p in doc["paths"]}
    by_exp = {p["unit"]: p for p in exp["paths"]}
    assert by_unit["log-rotate"]["path_exists"] == by_exp["log-rotate"]["path_exists"]
    assert (
        by_unit["deploy-artifact"]["path_exists"]
        == by_exp["deploy-artifact"]["path_exists"]
    )

    relocated = "/var/log/r2"
    dropin = ETC / "log-rotate.path.d" / "80-relocate.conf"
    snap = _snapshot_paths([dropin, REPORT])
    try:
        dropin.write_text(f"[Path]\nPathExists={relocated}\n")
        doc2 = _reseat()
        by2 = {p["unit"]: p for p in doc2["paths"]}
        assert by2["log-rotate"]["path_exists"] == relocated
        # No longer matches the durable tip, so it drops out of the armed set.
        assert by2["log-rotate"]["armed"] is False
    finally:
        _restore_paths(snap)
        if dropin.exists() and snap.get(str(dropin)) is None:
            dropin.unlink()
        _reseat()


def test_h8_amber() -> None:
    """Abort package preserved; live drop-in carries site-standard under a seal."""
    doc = _reseat()
    exp, _ = _expected_doc()
    assert ABORT.is_file()
    abort_kv = _parse_kv(ABORT.read_text())
    abort_pe = abort_kv.get("PathExists")
    assert abort_pe
    live_txt = LIVE_DROP.read_text()
    site_txt = SITE.read_text()
    assert "PathExists" not in _parse_kv(live_txt)
    assert _parse_kv(live_txt).get("Description") == _parse_kv(site_txt).get(
        "Description"
    )
    by_unit = {p["unit"]: p for p in doc["paths"]}
    by_exp = {p["unit"]: p for p in exp["paths"]}
    assert (
        by_unit["deploy-artifact"]["path_exists"]
        == by_exp["deploy-artifact"]["path_exists"]
    )
    assert by_unit["deploy-artifact"]["armed"] is True
    _reseat()
    assert ABORT.is_file()
    assert _parse_kv(ABORT.read_text()).get("PathExists") == abort_pe


def test_c1_flint() -> None:
    """Generation-bound receipt; a stale receipt rematerializes abort into the fold."""
    _reseat()
    rkv = _parse_kv(RECEIPT.read_text())
    assert rkv.get("gen") == GEN_TARGET.read_text().strip()
    assert rkv.get("mode") == "seal"
    assert "PathExists" not in _parse_kv(LIVE_DROP.read_text())
    abort_pe = _parse_kv(ABORT.read_text()).get("PathExists")
    assert abort_pe

    snap = _snapshot_paths([RECEIPT, GEN_TARGET, LIVE_DROP, REPORT])
    try:
        GEN_TARGET.write_text("8\n")
        RECEIPT.write_text("gen=7\nmode=seal\n")
        doc = _reseat()
        live_kv = _parse_kv(LIVE_DROP.read_text())
        assert live_kv.get("PathExists") == abort_pe
        by_unit = {p["unit"]: p for p in doc["paths"]}
        assert by_unit["deploy-artifact"]["path_exists"] == abort_pe
        assert by_unit["deploy-artifact"]["armed"] is False
    finally:
        _restore_paths(snap)
        RECEIPT.write_text(f"gen={GEN_TARGET.read_text().strip()}\nmode=seal\n")
        _reseat()


def test_u2_mica() -> None:
    """Trigger fire/retract reduction honors matching event id and arming."""
    doc = _reseat()
    by_trig = {t["unit"]: t for t in doc["triggers"]}
    assert by_trig["cert-bundle"]["last_epoch"] == 24
    assert by_trig["cert-bundle"]["honored"] is True
    assert by_trig["deploy-artifact"]["last_epoch"] == 20
    assert by_trig["deploy-artifact"]["honored"] is True
    assert by_trig["config-reload"]["honored"] is False
    assert by_trig["spool-flush"]["honored"] is False
    assert "log-rotate" not in by_trig


def test_k5_garnet() -> None:
    """Retracting one fire leaves a later fire on the same unit active."""
    snap = _snapshot_paths([TRIG, REPORT])
    try:
        TRIG.write_text(
            "\n".join(
                [
                    json.dumps(
                        {"kind": "fire", "eid": "k1", "unit": "deploy-artifact", "epoch": 30},
                        separators=(",", ":"),
                    ),
                    json.dumps(
                        {"kind": "fire", "eid": "k2", "unit": "deploy-artifact", "epoch": 33},
                        separators=(",", ":"),
                    ),
                    json.dumps(
                        {"kind": "retract", "eid": "k1", "epoch": 34},
                        separators=(",", ":"),
                    ),
                    json.dumps(
                        {"kind": "fire", "eid": "k3", "unit": "config-reload", "epoch": 31},
                        separators=(",", ":"),
                    ),
                    json.dumps(
                        {"kind": "retract", "eid": "k3", "epoch": 35},
                        separators=(",", ":"),
                    ),
                ]
            )
            + "\n"
        )
        doc = _reseat()
        by_trig = {t["unit"]: t for t in doc["triggers"]}
        assert by_trig["deploy-artifact"]["last_epoch"] == 33
        assert by_trig["deploy-artifact"]["honored"] is True
        assert "config-reload" not in by_trig
    finally:
        _restore_paths(snap)
        _reseat()


def test_x7_agate() -> None:
    """Interleaved fires and a retraction naming one unit's event id only."""
    snap = _snapshot_paths([TRIG, REPORT])
    try:
        TRIG.write_text(
            "\n".join(
                [
                    json.dumps(
                        {"kind": "fire", "eid": "x1", "unit": "cert-bundle", "epoch": 40},
                        separators=(",", ":"),
                    ),
                    json.dumps(
                        {"kind": "fire", "eid": "x2", "unit": "log-rotate", "epoch": 41},
                        separators=(",", ":"),
                    ),
                    json.dumps(
                        {"kind": "retract", "eid": "x1", "epoch": 42},
                        separators=(",", ":"),
                    ),
                    json.dumps(
                        {"kind": "fire", "eid": "x3", "unit": "cert-bundle", "epoch": 43},
                        separators=(",", ":"),
                    ),
                ]
            )
            + "\n"
        )
        doc = _reseat()
        exp, _ = _expected_doc()
        by_trig = {t["unit"]: t for t in doc["triggers"]}
        assert by_trig["cert-bundle"]["last_epoch"] == 43
        assert by_trig["cert-bundle"]["honored"] is True
        assert by_trig["log-rotate"]["last_epoch"] == 41
        assert by_trig["log-rotate"]["honored"] is True
        assert set(by_trig) == {"cert-bundle", "log-rotate"}
        assert doc["seat_ok"] is True
        by_unit = {p["unit"]: p for p in doc["paths"]}
        assert by_unit["cert-bundle"]["armed"] is True
        assert by_unit["log-rotate"]["armed"] is True
        assert by_unit["config-reload"]["armed"] is False
        assert by_unit["spool-flush"]["armed"] is False
        assert by_unit["cache-prime"]["armed"] is False
        assert doc["paths"] == exp["paths"]
    finally:
        _restore_paths(snap)
        _reseat()


def test_s8_zircon() -> None:
    """Clear output and derived live tables, re-enter, and match reconstruction."""
    snap = _snapshot_paths(
        [
            REPORT,
            LIVE / "fold.tsv",
            LIVE / "tip.tsv",
            LIVE / "arm.tsv",
            LIVE / "trig.tsv",
            ARMED_MAP,
        ]
    )
    try:
        REPORT.unlink(missing_ok=True)
        for name in ("fold.tsv", "tip.tsv", "arm.tsv", "trig.tsv"):
            p = LIVE / name
            if p.exists():
                p.unlink()
        if ARMED_MAP.exists():
            ARMED_MAP.unlink()
        doc = _reseat()
        exp, _ = _expected_doc()
        assert doc == exp
        _assert_armed_map(doc)
    finally:
        _restore_paths(snap)
        _reseat()


def test_t4_pearl() -> None:
    """Surface WATCH-OK is insufficient; the deep armed set differs from the probe."""
    doc = _reseat()
    assert doc["seat_ok"] is True
    health = _run(["/usr/local/bin/pathhealth"], check=False)
    assert health.returncode == 0
    assert health.stdout.strip() == "WATCH-OK"
    armed = {p["unit"] for p in doc["paths"] if p["armed"]}
    assert armed == {"cert-bundle", "deploy-artifact", "log-rotate"}
    loaded = {
        line.split()[0]
        for line in LOADED_MAP.read_text().splitlines()
        if line.strip()
    }
    assert "config-reload" in loaded
    assert "config-reload" not in armed
    map_kv = _parse_kv(ARMED_MAP.read_text())
    assert "config-reload" not in map_kv
    assert "cert-bundle" in map_kv


def test_m1_opal() -> None:
    """Full arming matrix equality across fold, tip, floor, watchgen, and bait."""
    doc = _reseat()
    exp, _ = _expected_doc()
    assert doc["paths"] == exp["paths"]
    by_unit = {p["unit"]: p for p in doc["paths"]}
    by_exp = {p["unit"]: p for p in exp["paths"]}
    assert by_unit["deploy-artifact"]["armed"] is True
    assert by_unit["cert-bundle"]["armed"] is True
    assert by_unit["config-reload"]["armed"] is False
    assert by_unit["spool-flush"]["armed"] is False
    assert by_unit["cache-prime"]["armed"] is False
    assert by_unit["log-rotate"]["armed"] is True
    assert by_unit["cert-bundle"]["path_changed"] == by_exp["cert-bundle"]["path_changed"]
    assert by_exp["cert-bundle"]["path_changed"]
