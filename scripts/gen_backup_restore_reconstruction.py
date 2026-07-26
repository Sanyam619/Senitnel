#!/usr/bin/env python3
"""Regenerate backup-restore-reconstruction lab fixtures and test constants."""

from __future__ import annotations

import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks" / "backup-restore-reconstruction"
ENV = TASK / "environment"
LABS = ENV / "labs"


def stamp(data: bytes) -> str:
    a = 0xCBF29CE484222325
    b = 0x9E3779B97F4A7C15
    for i, byte in enumerate(data):
        a ^= byte
        a = (a * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
        b ^= ((byte << ((i % 8) * 8)) ^ i) & 0xFFFFFFFFFFFFFFFF
        b = ((b << 7) | (b >> 57)) & 0xFFFFFFFFFFFFFFFF
        b = (b + (a ^ 0x517CC1B727220A95)) & 0xFFFFFFFFFFFFFFFF
    return f"{a:016x}{b:016x}"


def part(part_id: str, data: bytes) -> dict:
    return {"id": part_id, "data": data, "len": len(data), "mark": stamp(data)}


SPANS = {
    "a01": part("a01", b"atlas alpha line one\n"),
    "a02": part("a02", b"cargo crates staged on pier seven\n"),
    "a03": part("a03", b"end atlas manifest\n"),
    "a04": part("a04", b"window open\n"),
    "a05": part("a05", b"sorted archive shelf\n"),
    "a06": part("a06", b"window closed\n"),
    "a07": part("a07", b"baseline atlas note\n"),
    "b01": part("b01", b"beacon uplink start\n"),
    "b02": part("b02", b"signal cabinet green\n"),
    "b03": part("b03", b"uplink stop\n"),
    "b04": part("b04", b"route card alpha\n"),
    "b05": part("b05", b"route card beta\n"),
    "b06": part("b06", b"baseline beacon note\n"),
    "c01": part("c01", b"cinder ledger top\n"),
    "c02": part("c02", b"ash crate count eight\n"),
    "c03": part("c03", b"quarry spare coil sealed\n"),
    "c04": part("c04", b"ledger close\n"),
    "c05": part("c05", b"baseline cinder note\n"),
    "r01": part("r01", b"ridge camp opening note\n"),
    "r02": part("r02", b"supply sled moved downslope\n"),
    "r03": part("r03", b"ridge camp closing note\n"),
    "r04": part("r04", b"relay borrow from beacon shelf\n"),
    "m01": part("m01", b"mesa radio check-in open\n"),
    "m02": part("m02", b"mesa camp relay staging yard line\n"),
    "m02a": part("m02a", b"mesa camp relay "),
    "m02b": part("m02b", b"staging yard line\n"),
    "m03": part("m03", b"mesa baseline anchor note\n"),
    "m04": part("m04", b"mesa atlas shelf echo marker\n"),
}


def xor_bytes(data: bytes, key: int) -> bytes:
    return bytes(b ^ key for b in data)


def decoy(data: bytes) -> bytes:
    if not data:
        return data
    tail = data[-1:]
    repl = b"X" if tail != b"X" else b"Y"
    return data[:-1] + repl


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def recipe(name: str, files: list[tuple[str, list[str]]]) -> str:
    lines = [f"# name {name}"]
    for path, part_ids in files:
        lines.append(f"file {path}")
        for pid in part_ids:
            p = SPANS[pid]
            lines.append(f"part {pid} {p['len']} {p['mark']}")
    return "\n".join(lines) + "\n"


def index(rows: list[tuple[str, str, int, int]]) -> str:
    lines = ["# local span locator table"]
    for pid, obj, off, ln in rows:
        lines.append(f"{pid}|{obj}|{off}|{ln}")
    return "\n".join(lines) + "\n"


def build_atlas() -> None:
    repo = LABS / "atlas"
    a02 = SPANS["a02"]["data"]
    a02_decoy = decoy(a02)
    pool_a = b"AA" + SPANS["a01"]["data"] + a02_decoy + a02 + SPANS["a03"]["data"] + b"ZZ"
    off_a01 = 2
    off_a02_decoy = 2 + len(SPANS["a01"]["data"])
    off_a02 = off_a02_decoy + len(a02_decoy)
    off_a03 = off_a02 + len(a02)
    pool_b = (
        b"BB"
        + SPANS["a04"]["data"]
        + SPANS["a05"]["data"]
        + SPANS["a06"]["data"]
        + SPANS["a07"]["data"]
        + b"|mesa|"
        + SPANS["m04"]["data"]
        + b"YY"
    )
    off_m04 = pool_b.index(b"|mesa|") + len(b"|mesa|")
    write(repo / "objects/pool-a.blob", pool_a.decode("utf-8"))
    write(repo / "objects/pool-b.blob", pool_b.decode("utf-8"))
    write(
        repo / "index/chunks.idx",
        index([
            ("a01", "pool-a.blob", off_a01, SPANS["a01"]["len"]),
            ("a02", "pool-a.blob", off_a02_decoy, len(a02_decoy)),
            ("a03", "pool-a.blob", off_a03, SPANS["a03"]["len"]),
            ("a04", "pool-b.blob", 2, SPANS["a04"]["len"]),
            ("a05", "pool-b.blob", 14, SPANS["a05"]["len"]),
            ("a06", "pool-b.blob", 35, SPANS["a06"]["len"]),
            ("a07", "pool-b.blob", 49, SPANS["a07"]["len"]),
            ("m04", "pool-b.blob", off_m04, SPANS["m04"]["len"]),
        ]),
    )
    for snap, files in [
        ("fieldday-2026-06-18", [("home/manifest.txt", ["a01", "a02", "a03"]), ("home/window.log", ["a04", "a05", "a06"])]),
        ("steady-2026-06-17", [("home/manifest.txt", ["a01", "a07", "a03"]), ("home/window.log", ["a04", "a05", "a06"])]),
    ]:
        write(repo / f"recipes/{snap}.rec", recipe(snap, files))
    write(repo / "journal/compact.log", "atlas: compaction shifted pier-seven span boundaries\n")


def build_beacon() -> None:
    repo = LABS / "beacon"
    b05 = SPANS["b05"]["data"]
    b05_decoy = decoy(b05)
    r04 = SPANS["r04"]["data"]
    pool_a = b"123" + SPANS["b01"]["data"] + SPANS["b02"]["data"] + SPANS["b03"]["data"] + b"456"
    pool_b = (
        b"xyz"
        + SPANS["b04"]["data"]
        + b05_decoy
        + b05
        + SPANS["b06"]["data"]
        + b"|relay|"
        + r04
        + b"|end"
    )
    off_b04 = 3
    off_b05_decoy = off_b04 + len(SPANS["b04"]["data"])
    off_b05 = off_b05_decoy + len(b05_decoy)
    off_b06 = off_b05 + len(b05)
    off_r04 = pool_b.index(b"|relay|") + len(b"|relay|")
    write(repo / "objects/pool-a.blob", pool_a.decode("utf-8"))
    write(repo / "objects/pool-b.blob", pool_b.decode("utf-8"))
    write(
        repo / "index/chunks.idx",
        index([
            ("b01", "pool-a.blob", 3, SPANS["b01"]["len"]),
            ("b02", "pool-a.blob", 23, SPANS["b02"]["len"]),
            ("b03", "pool-a.blob", 44, SPANS["b03"]["len"]),
            ("b04", "pool-b.blob", off_b04, SPANS["b04"]["len"]),
            ("b05", "pool-b.blob", off_b05_decoy, len(b05_decoy)),
            ("b06", "pool-b.blob", off_b06, SPANS["b06"]["len"]),
            ("r04", "pool-b.blob", off_r04, SPANS["r04"]["len"]),
        ]),
    )
    for snap, files in [
        ("fieldday-2026-06-18", [("logs/uplink.txt", ["b01", "b02", "b03"]), ("logs/routes.txt", ["b04", "b05"])]),
        ("steady-2026-06-17", [("logs/uplink.txt", ["b01", "b06", "b03"]), ("logs/routes.txt", ["b04", "b05"])]),
    ]:
        write(repo / f"recipes/{snap}.rec", recipe(snap, files))
    write(repo / "journal/compact.log", "beacon: route-card span retained for ridge borrow inventory\n")


def build_cinder() -> None:
    repo = LABS / "cinder"
    c03 = SPANS["c03"]["data"]
    c03_decoy = decoy(c03)
    pool_a = b"cA" + SPANS["c01"]["data"] + SPANS["c02"]["data"] + SPANS["c04"]["data"] + SPANS["c05"]["data"] + b"cZ"
    pool_b = b"carry:" + c03_decoy + c03 + b":after"
    off_c01 = 2
    off_c02 = off_c01 + len(SPANS["c01"]["data"])
    off_c04 = off_c02 + len(SPANS["c02"]["data"])
    off_c05 = off_c04 + len(SPANS["c04"]["data"])
    off_c03_decoy = len(b"carry:")
    off_c03 = off_c03_decoy + len(c03_decoy)
    write(repo / "objects/pool-a.blob", pool_a.decode("utf-8"))
    write(repo / "objects/pool-b.blob", pool_b.decode("utf-8"))
    write(
        repo / "index/chunks.idx",
        index([
            ("c01", "pool-a.blob", off_c01, SPANS["c01"]["len"]),
            ("c02", "pool-a.blob", off_c02, SPANS["c02"]["len"]),
            ("c03", "pool-old.blob", 0, SPANS["c03"]["len"]),
            ("c03dup", "pool-b.blob", off_c03_decoy, len(c03_decoy)),
            ("c04", "pool-a.blob", off_c04, SPANS["c04"]["len"]),
            ("c05", "pool-a.blob", off_c05, SPANS["c05"]["len"]),
        ]),
    )
    for snap, files in [
        ("fieldday-2026-06-18", [("ledger/day.txt", ["c01", "c02", "c03", "c04"])]),
        ("steady-2026-06-17", [("ledger/day.txt", ["c01", "c03", "c05"])]),
    ]:
        write(repo / f"recipes/{snap}.rec", recipe(snap, files))
    write(repo / "journal/compact.log", "cinder: pruned pool-old after duplicate coil span landed in pool-b\n")
    write(repo / "ledger/borrow.list", "")


def build_ridge() -> None:
    repo = LABS / "ridge"
    r02 = SPANS["r02"]["data"]
    r02_decoy = decoy(r02)
    pool_a = b"RR" + SPANS["r01"]["data"] + r02_decoy + r02 + SPANS["r03"]["data"] + b"RR"
    off_r01 = 2
    off_r02_decoy = off_r01 + len(SPANS["r01"]["data"])
    off_r02 = off_r02_decoy + len(r02_decoy)
    off_r03 = off_r02 + len(r02)
    write(repo / "objects/pool-a.blob", pool_a.decode("utf-8"))
    write(repo / "objects/pool-b.blob", "ridge-local-empty\n")
    write(
        repo / "index/chunks.idx",
        index([
            ("r01", "pool-a.blob", off_r01, SPANS["r01"]["len"]),
            ("r02", "pool-a.blob", off_r02_decoy, len(r02_decoy)),
            ("r03", "pool-a.blob", off_r03, SPANS["r03"]["len"]),
            ("r04", "pool-c.blob", 0, SPANS["r04"]["len"]),
        ]),
    )
    for snap, files in [
        ("fieldday-2026-06-18", [("trail/summary.txt", ["r01", "r02", "r03"]), ("trail/borrow.txt", ["r04"])]),
        ("steady-2026-06-17", [("trail/summary.txt", ["r01", "r03"]), ("trail/borrow.txt", ["r04"])]),
    ]:
        write(repo / f"recipes/{snap}.rec", recipe(snap, files))
    write(repo / "journal/compact.log", "ridge: borrow span inventory references external shelf\n")
    write(repo / "ledger/borrow.list", "beacon\n")


def build_mesa() -> None:
    repo = LABS / "mesa"
    mask = 0x59
    m01 = SPANS["m01"]["data"]
    m02 = SPANS["m02"]["data"]
    m02_decoy = decoy(m02)
    pool_a = b"MM" + xor_bytes(m01, mask) + b"MM"
    off_m01 = 2
    off_m02_decoy = off_m01 + len(m01)
    pool_b = b"NN" + SPANS["m02a"]["data"] + SPANS["m02b"]["data"] + SPANS["m03"]["data"] + b"NN"
    off_m02a = 2
    off_m02b = off_m02a + len(SPANS["m02a"]["data"])
    off_m03 = off_m02b + len(SPANS["m02b"]["data"])
    write(repo / "objects/pool-a.blob", pool_a.decode("latin-1"))
    write(repo / "objects/pool-b.blob", pool_b.decode("utf-8"))
    write(
        repo / "index/chunks.idx",
        index([
            ("m01", "pool-a.blob", off_m01, SPANS["m01"]["len"]),
            ("m02", "pool-a.blob", off_m02_decoy, len(m02_decoy)),
            ("m02a", "pool-b.blob", off_m02a, SPANS["m02a"]["len"]),
            ("m02b", "pool-b.blob", off_m02b, SPANS["m02b"]["len"]),
            ("m03", "pool-b.blob", off_m03, SPANS["m03"]["len"]),
            ("m04", "pool-remote.blob", 0, SPANS["m04"]["len"]),
        ]),
    )
    for snap, files in [
        ("fieldday-2026-06-18", [("ops/radio.txt", ["m01", "m02"]), ("ops/relay.txt", ["m04"])]),
        ("steady-2026-06-17", [("ops/radio.txt", ["m01", "m03"]), ("ops/relay.txt", ["m04"])]),
    ]:
        write(repo / f"recipes/{snap}.rec", recipe(snap, files))
    write(repo / "journal/compact.log", "mesa: masked pool-a shelf and split radio span fragments in pool-b\n")
    write(repo / "ledger/borrow.list", "atlas,beacon,cinder,ridge\n")
    write(repo / "ledger/fragments.map", "m02|m02a|m02b\n")


def build_profiles() -> None:
    write(ENV / "profiles/site-a.conf", "name=atlas\nretain_days=14\ncompact_after=4\npool_order=pool-a,pool-b\n")
    write(ENV / "profiles/site-b.conf", "name=beacon\nretain_days=10\ncompact_after=3\npool_order=pool-b,pool-a\n")
    write(ENV / "profiles/site-c.conf", "name=cinder\nretain_days=12\ncompact_after=5\npool_order=pool-b,pool-a\n")
    write(
        ENV / "profiles/site-d.conf",
        "name=ridge\nretain_days=8\ncompact_after=2\npool_order=pool-b,pool-a\nscan_order=beacon,cinder,atlas,ridge\n",
    )
    write(
        ENV / "profiles/site-e.conf",
        "name=mesa\nretain_days=6\ncompact_after=2\nmask_key=89\nmasked_pools=pool-a\npool_order=pool-b,pool-a\nscan_order=atlas,beacon,cinder,ridge,mesa\n",
    )


def build_docs() -> None:
    write(
        ENV / "docs/layout.md",
        textwrap.dedent(
            """\
            # Local storage layout

            Each lab directory (atlas, beacon, cinder, ridge, mesa) contains `recipes/`, `index/`, `objects/`, `journal/`, and optional `ledger/`.
            Recipe rows list file material in small spans with part identifiers (for example a01, r04, or m02), length, and mark fields. The index maps span
            identifiers to object byte ranges. Object files are append-only pools used by ordinary restore
            and inventory operations. Some repositories keep a `ledger/borrow.list` naming other labs that
            may hold equivalent shelf bytes, and a `ledger/fragments.map` listing split spans that must be
            merged in order. Site profiles may declare mask_key and masked_pools for masked object pools. Rolling cut markers
            over pool bytes can narrow alignment walks. Report status labels distinguish indexed locator reads,
            scanned pool recovery, and merged fragment assembly.
            """
        ),
    )


def render_tests() -> str:
    parts = []
    for key in sorted(SPANS):
        val = SPANS[key]["data"].decode("utf-8")
        esc = val.replace("\\", "\\\\").replace("\n", "\\n")
        parts.append(f'{key.upper()} = "{esc}"')
    part_block = "\n".join(parts)
    return f'''import json
import shutil
import subprocess
from pathlib import Path

APP = Path("/app")
OUT = APP / "restore" / "fieldday-2026-06-18"
REPORT = APP / "repair.json"

{part_block}


def _k(a, b, c):
    return "/".join([a, b, c])

ATLAS_MAIN = _k("atlas", "home", "manifest.txt")
ATLAS_SIDE = _k("atlas", "home", "window.log")
BEACON_MAIN = _k("beacon", "logs", "uplink.txt")
BEACON_SIDE = _k("beacon", "logs", "routes.txt")
CINDER_MAIN = _k("cinder", "ledger", "day.txt")
RIDGE_MAIN = _k("ridge", "trail", "summary.txt")
RIDGE_BORROW = _k("ridge", "trail", "borrow.txt")
MESA_RADIO = _k("mesa", "ops", "radio.txt")
MESA_RELAY = _k("mesa", "ops", "relay.txt")

EXPECTED = {{
    ATLAS_MAIN: A01 + A02 + A03,
    ATLAS_SIDE: A04 + A05 + A06,
    BEACON_MAIN: B01 + B02 + B03,
    BEACON_SIDE: B04 + B05,
    CINDER_MAIN: C01 + C02 + C03 + C04,
    RIDGE_MAIN: R01 + R02 + R03,
    RIDGE_BORROW: R04,
    MESA_RADIO: M01 + M02,
    MESA_RELAY: M04,
}}

NEIGHBOR = {{
    ATLAS_MAIN: A01 + A07 + A03,
    BEACON_MAIN: B01 + B06 + B03,
    CINDER_MAIN: C01 + C03 + C05,
    RIDGE_MAIN: R01 + R03,
    RIDGE_BORROW: R04,
    MESA_RADIO: M01 + M03,
    MESA_RELAY: M04,
}}


def _text(rel):
    return (OUT / rel).read_text()


def _report():
    return json.loads(REPORT.read_text())


def test_case_a():
    """The atlas manifest is rebuilt from its original byte spans."""
    assert _text(ATLAS_MAIN) == EXPECTED[ATLAS_MAIN]


def test_case_b():
    """The second atlas file is present with no shifted bytes."""
    assert _text(ATLAS_SIDE) == EXPECTED[ATLAS_SIDE]


def test_case_c():
    """Both beacon files match the stored snapshot material."""
    assert _text(BEACON_MAIN) == EXPECTED[BEACON_MAIN]
    assert _text(BEACON_SIDE) == EXPECTED[BEACON_SIDE]


def test_case_d():
    """The cinder ledger includes the span absent from its ordinary location."""
    assert _text(CINDER_MAIN) == EXPECTED[CINDER_MAIN]


def test_case_e():
    """The reconstructed tree has exactly the expected repository paths."""
    found = sorted(str(p.relative_to(OUT)) for p in OUT.rglob("*") if p.is_file())
    assert found == sorted(EXPECTED)


def test_case_f():
    """The report records ordinary and searched provenance for materialized spans."""
    data = _report()
    assert data["target"] == "fieldday-2026-06-18"
    rows = [row for items in data["repositories"].values() for row in items]
    assert rows
    assert {{"indexed", "scanned", "merged"}} <= {{row["status"] for row in rows}}
    for row in rows:
        assert set(row) >= {{"path", "span", "bytes", "status", "source"}}
        assert isinstance(row["bytes"], int) and row["bytes"] > 0


def test_case_g():
    """Each repository reports at least one span found outside the ordinary location."""
    data = _report()
    scanned = {{repo for repo, rows in data["repositories"].items() for row in rows if row["status"] in {{"scanned", "merged"}}}}
    assert scanned == {{"atlas", "beacon", "cinder", "ridge", "mesa"}}
    cinder_rows = next(rows for repo, rows in data["repositories"].items() if repo == "cinder")
    assert any(row["path"] == "ledger/day.txt" for row in cinder_rows if row["status"] == "scanned")


def test_case_h():
    """The input metadata still names the cinder span and its pool remains nonempty."""
    recipe = APP / "labs" / "cinder" / "recipes" / "fieldday-2026-06-18.rec"
    pool = APP / "labs" / "cinder" / "objects" / "pool-b.blob"
    assert "part c03 " in recipe.read_text()
    assert pool.stat().st_size > 16


def test_case_i(tmp_path):
    """Neighboring snapshots still restore through the Rust utility."""
    side = tmp_path / "n1"
    log = tmp_path / "n2.json"
    subprocess.run([
        "cargo", "run", "--quiet", "--", "run",
        "--root", "/app/labs",
        "--name", "steady-2026-06-17",
        "--out", str(side),
        "--log", str(log),
    ], cwd=APP, check=True, timeout=60)
    for rel, value in NEIGHBOR.items():
        assert (side / rel).read_text() == value


def test_case_j(tmp_path):
    """Copying the reconstructed tree preserves content and report cardinality."""
    clone = tmp_path / "n3"
    shutil.copytree(OUT, clone)
    for rel, value in EXPECTED.items():
        assert (clone / rel).read_text() == value
    sizes = {{repo: len(rows) for repo, rows in _report()["repositories"].items()}}
    assert sizes == {{"atlas": 6, "beacon": 5, "cinder": 4, "ridge": 4, "mesa": 3}}


def test_case_k():
    """The ridge summary file restores all three camp spans in order."""
    assert _text(RIDGE_MAIN) == EXPECTED[RIDGE_MAIN]


def test_case_l():
    """The ridge borrow file restores bytes held on another lab shelf."""
    assert _text(RIDGE_BORROW) == EXPECTED[RIDGE_BORROW]


def test_case_m():
    """Cross-lab recovery names the supplying repository in report sources."""
    data = _report()
    ridge_rows = data["repositories"]["ridge"]
    borrow_rows = [row for row in ridge_rows if row["span"] == "r04"]
    assert len(borrow_rows) == 1
    assert borrow_rows[0]["status"] == "scanned"
    assert "beacon" in borrow_rows[0]["source"]


def test_case_n():
    """The mesa radio file restores masked and merged spans."""
    assert _text(MESA_RADIO) == EXPECTED[MESA_RADIO]


def test_case_o():
    """The mesa relay file restores bytes from another lab shelf."""
    assert _text(MESA_RELAY) == EXPECTED[MESA_RELAY]


def test_case_p():
    """Split spans report merged provenance in the repair log."""
    data = _report()
    mesa_rows = data["repositories"]["mesa"]
    merged = [row for row in mesa_rows if row["span"] == "m02"]
    assert len(merged) == 1
    assert merged[0]["status"] == "merged"
    assert "m02a" in merged[0]["source"] and "m02b" in merged[0]["source"]


def test_case_q():
    """Cross-lab mesa recovery names atlas in report sources."""
    data = _report()
    mesa_rows = data["repositories"]["mesa"]
    relay_rows = [row for row in mesa_rows if row["span"] == "m04"]
    assert len(relay_rows) == 1
    assert relay_rows[0]["status"] == "scanned"
    assert "atlas" in relay_rows[0]["source"]
'''


def write_fixture_checksums() -> None:
    import hashlib

    rows = []
    for path in sorted(p for p in LABS.rglob("*") if p.is_file() and p.name != ".fixture_checksums.sha256"):
        rel = path.relative_to(LABS).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append(f"{digest}  {rel}")
    (LABS / ".fixture_checksums.sha256").write_text("\n".join(rows) + "\n")


def main() -> None:
    build_atlas()
    build_beacon()
    build_cinder()
    build_ridge()
    build_mesa()
    build_profiles()
    build_docs()
    write_fixture_checksums()
    print(f"generated fixtures under {LABS}")
    print("note: tests/test_outputs.py is maintained separately (descriptive names + provenance)")


if __name__ == "__main__":
    main()
