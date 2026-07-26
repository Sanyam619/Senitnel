"""Verifier for nftables ruleset generation cutover seating."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

OUT = Path("/output/nft-seat.json")
ROSTER = Path("/etc/nft/roster.list")
FLOOR_D = Path("/var/lib/nft/floors")
PREFER = Path("/var/lib/nft/ops/prefer.conf")
JOURNAL = Path("/var/lib/nft/ops/journal.jsonl")
GEN_TARGET = Path("/var/lib/nft/state/gen.target")
FOLD = Path("/var/lib/nft/ops/fold.nft")
APPLIED = Path("/var/lib/nft/ops/applied.nft")
KERNEL = Path("/var/lib/nft/ops/kernel.nft")
LIVE_90 = Path("/etc/nftables.d/90-local.nft")
ABORT_PKG = Path("/var/lib/nft/ops/abort.d/90-local.nft")
RECEIPT = Path("/var/lib/nft/state/cutover.ok")
FRAG_D = Path("/etc/nftables.d")
DATA_NFT = Path("/app/data/nft")
FRAG_MAP = Path("/var/lib/nft/state/frag_map.tsv")

FAM = {"filter": "inet", "nat": "ip", "mangle": "ip", "raw": "ip"}


def _run_seat() -> None:
    subprocess.run(["/app/ops/run_nft_seat.sh"], check=False)


def _normalize(text: str) -> str:
    lines = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        lines.append(" ".join(line.split()))
    return "\n".join(lines) + ("\n" if lines else "")


def _load_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _roster() -> list[str]:
    return [
        ln.strip()
        for ln in ROSTER.read_text().splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]


def _sealed_tips() -> dict[str, int]:
    target = int(GEN_TARGET.read_text().strip())
    tips: dict[str, int] = {}
    for line in JOURNAL.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if (
            row.get("kind") == "cutover"
            and int(row.get("gen", -1)) == target
            and row.get("mode") == "seal"
        ):
            tips = {k: int(v) for k, v in row.get("tips", {}).items()}
    return tips


def _frag_map() -> dict[str, str]:
    out: dict[str, str] = {}
    for line in FRAG_MAP.read_text().splitlines():
        parts = line.split()
        if len(parts) >= 2:
            out[parts[0]] = parts[1]
    return out


def _count_rules(text: str) -> int:
    n = 0
    for line in text.splitlines():
        s = line.split("#", 1)[0].strip()
        if not s or s in ("{", "}"):
            continue
        if s.startswith(("table ", "chain ")):
            continue
        if re.match(r"^type\s+\S+\s+hook\s+", s):
            continue
        n += 1
    return n


def _parse_chains(text: str) -> list[dict]:
    chains: list[dict] = []
    cur_table = None
    cur_chain = None
    for raw in text.splitlines():
        s = raw.split("#", 1)[0].strip()
        if not s:
            continue
        m = re.match(r"^table\s+(\S+)\s+(\S+)\s*\{?", s)
        if m:
            cur_table = m.group(2)
            continue
        m = re.match(r"^chain\s+(\S+)\s*\{?", s)
        if m:
            cur_chain = m.group(1)
            continue
        m = re.match(
            r"^type\s+(\S+)\s+hook\s+(\S+)\s+priority\s+(-?\d+)\s*;\s*policy\s+(\S+)\s*;",
            s,
        )
        if m and cur_table and cur_chain:
            chains.append(
                {
                    "table": cur_table,
                    "name": cur_chain,
                    "policy": m.group(4).rstrip(";"),
                    "hook": m.group(2),
                    "priority": int(m.group(3)),
                }
            )
    return chains


def _expected_fold() -> str:
    tips = _sealed_tips()
    fmap = _frag_map()
    prefer = _load_kv(PREFER)
    chunks: list[str] = []
    for f in sorted(FRAG_D.glob("*.nft")):
        body = f.read_text()
        if "abort_lab" in body:
            continue
        table = fmap.get(f.name)
        if table is not None:
            tip = int(tips.get(table, 0))
            floor = int((FLOOR_D / f"{table}.floor").read_text().strip())
            if tip < floor:
                continue
        # Prefer-pin base policies on included bodies sourced from templates.
        src_name = f.name
        if src_name in fmap and (DATA_NFT / src_name).is_file():
            body = (DATA_NFT / src_name).read_text()
        text = body
        cur_family = None
        cur_table = None
        cur_chain = None
        out_lines: list[str] = []
        for raw in text.splitlines():
            s = raw.split("#", 1)[0].strip()
            m = re.match(r"^table\s+(\S+)\s+(\S+)", s)
            if m:
                cur_family, cur_table = m.group(1), m.group(2)
                cur_chain = None
                out_lines.append(raw)
                continue
            m = re.match(r"^chain\s+(\S+)", s)
            if m:
                cur_chain = m.group(1)
                out_lines.append(raw)
                continue
            m = re.match(
                r"^(type\s+\S+\s+hook\s+\S+\s+priority\s+-?\d+\s*;\s*policy\s+)(\S+)(\s*;.*)$",
                s,
            )
            if m and cur_family and cur_table and cur_chain:
                key = f"{cur_family}/{cur_table}/{cur_chain}"
                if key in prefer:
                    indent = raw[: len(raw) - len(raw.lstrip())]
                    out_lines.append(f"{indent}{m.group(1)}{prefer[key]}{m.group(3)}")
                    continue
            out_lines.append(raw)
        chunks.append("\n".join(out_lines).rstrip() + "\n")
    return "\n".join(chunks) if chunks else ""


def _expected_doc() -> dict:
    tips = _sealed_tips()
    fold = _expected_fold()
    tables = [
        {"family": FAM[name], "name": name, "generation": int(tips.get(name, 0))}
        for name in _roster()
    ]
    return {
        "schema_tag": "nft-seat-v1",
        "tables": tables,
        "chains": _parse_chains(fold),
        "rules_applied": _count_rules(fold),
        "seat_ok": True,
    }


@pytest.fixture(scope="module", autouse=True)
def _seat_twice() -> None:
    if OUT.exists():
        OUT.unlink()
    _run_seat()
    first = OUT.read_bytes() if OUT.exists() else b""
    _run_seat()
    second = OUT.read_bytes() if OUT.exists() else b""
    Path("/tmp/seat_first.bin").write_bytes(first)
    Path("/tmp/seat_second.bin").write_bytes(second)


def _doc() -> dict:
    assert OUT.is_file(), "missing /output/nft-seat.json"
    return json.loads(OUT.read_text())


def test_q3_topaz() -> None:
    """Ledger schema, schema_tag, and seat_ok."""
    doc = _doc()
    assert doc["schema_tag"] == "nft-seat-v1"
    assert isinstance(doc["tables"], list) and len(doc["tables"]) == len(_roster())
    assert isinstance(doc["chains"], list)
    assert isinstance(doc["rules_applied"], int)
    assert doc["seat_ok"] is True
    for t in doc["tables"]:
        assert set(t) >= {"family", "name", "generation"}
        assert isinstance(t["generation"], int)
    for c in doc["chains"]:
        assert set(c) >= {"table", "name", "policy", "hook", "priority"}
        assert isinstance(c["priority"], int)


def test_n4_beryl() -> None:
    """Two seating passes leave byte-identical output and stable live gen."""
    a = Path("/tmp/seat_first.bin").read_bytes()
    b = Path("/tmp/seat_second.bin").read_bytes()
    assert a and b and a == b
    live = Path("/var/lib/nft/state/gen.live").read_text().strip()
    assert live == GEN_TARGET.read_text().strip()


def test_w7_quartz() -> None:
    """Frozen fixtures under /app/data/nft remain packaging-pinned."""
    pin = Path("/app/packaging/nft.sha256")
    assert pin.is_file()
    proc = subprocess.run(
        ["sha256sum", "-c", "/app/packaging/nft.sha256"],
        cwd="/app/data/nft",
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr


def test_j2_onyx() -> None:
    """Lexical fold excludes abort overlay; live 90 stays a clean fragment."""
    _run_seat()
    fold = FOLD.read_text()
    assert "abort_lab" not in fold
    # Operator memo key=value lines must not be folded as nftables rules.
    assert "tip_policy=" not in fold
    assert "bind_order=" not in fold
    assert LIVE_90.is_file()
    assert "abort_lab" not in LIVE_90.read_text()
    assert "tip_policy=" not in LIVE_90.read_text()
    assert ABORT_PKG.is_file()
    assert "abort_lab" in ABORT_PKG.read_text()


def test_v5_coral() -> None:
    """Base-chain policies match durable prefer, not surface accept decoy."""
    _run_seat()
    prefer = _load_kv(PREFER)
    surface = _load_kv(Path("/etc/nft/surface_prefer.conf"))
    assert prefer.get("inet/filter/input") == "drop"
    assert surface.get("inet/filter/input") == "accept"
    chains = {(c["table"], c["name"]): c for c in _doc()["chains"]}
    assert chains[("filter", "input")]["policy"] == "drop"
    assert chains[("filter", "forward")]["policy"] == "drop"
    assert chains[("filter", "output")]["policy"] == "accept"
    assert ("raw", "prerouting") not in chains


def test_p9_jade() -> None:
    """Under-floor table omitted from fold/chains but still listed in tables."""
    tips = _sealed_tips()
    assert tips["raw"] < int((FLOOR_D / "raw.floor").read_text().strip())
    _run_seat()
    fold = FOLD.read_text()
    assert "table ip raw" not in fold
    doc = _doc()
    assert all(c["table"] != "raw" for c in doc["chains"])
    by_name = {t["name"]: t for t in doc["tables"]}
    assert "raw" in by_name
    assert by_name["raw"]["generation"] == tips["raw"]
    assert len(doc["tables"]) == len(_roster())


def test_h8_amber() -> None:
    """applied.nft and kernel ruleset match the durable fold."""
    _run_seat()
    exp = _normalize(_expected_fold())
    assert exp
    assert _normalize(FOLD.read_text()) == exp
    assert _normalize(APPLIED.read_text()) == exp
    assert _normalize(KERNEL.read_text()) == exp


def test_c1_flint() -> None:
    """Matching cutover.ok receipt; gen.live aligned to target."""
    assert RECEIPT.is_file()
    kv = _load_kv(RECEIPT)
    target = GEN_TARGET.read_text().strip()
    assert kv.get("gen") == target
    assert kv.get("mode") == "seal"
    live = Path("/var/lib/nft/state/gen.live").read_text().strip()
    assert live == target


def test_r6_slate() -> None:
    """rules_applied matches durable fold rule count (blocks append inflation)."""
    _run_seat()
    doc = _doc()
    exp = _expected_doc()
    assert doc["rules_applied"] == exp["rules_applied"]
    assert doc["rules_applied"] == _count_rules(KERNEL.read_text())
    assert doc["rules_applied"] > 0


def test_u2_mica() -> None:
    """Full tables/chains matrix against durable authority."""
    doc = _doc()
    exp = _expected_doc()
    assert doc["tables"] == exp["tables"]
    assert sorted(doc["chains"], key=lambda c: (c["table"], c["name"])) == sorted(
        exp["chains"], key=lambda c: (c["table"], c["name"])
    )
    assert doc["rules_applied"] == exp["rules_applied"]
    assert doc["seat_ok"] is True
    by_name = {t["name"]: t for t in doc["tables"]}
    assert by_name["filter"]["generation"] == 7
    assert by_name["nat"]["generation"] == 5
    assert by_name["mangle"]["generation"] == 6
    assert by_name["raw"]["generation"] == 4


def test_m1_opal() -> None:
    """Surface fwhealth may print active; deep seating still required."""
    proc = subprocess.run(
        ["/usr/local/bin/fwhealth"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "active" in proc.stdout
    doc = _doc()
    assert doc["seat_ok"] is True
    assert doc["schema_tag"] == "nft-seat-v1"
    # Surface active alone is not enough — durable prefer must still show.
    chains = {(c["table"], c["name"]): c["policy"] for c in doc["chains"]}
    assert chains.get(("filter", "input")) == "drop"
    live = Path("/var/lib/nft/state/gen.live").read_text().strip()
    assert live == GEN_TARGET.read_text().strip()


def test_t4_pearl() -> None:
    """Second apply keeps rules_applied stable (atomic replace, not append)."""
    _run_seat()
    first = _doc()["rules_applied"]
    _run_seat()
    second = _doc()["rules_applied"]
    assert first == second == _expected_doc()["rules_applied"]
    assert _normalize(KERNEL.read_text()) == _normalize(_expected_fold())
