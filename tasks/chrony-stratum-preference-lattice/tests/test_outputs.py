"""Verifier for chrony-stratum-preference-lattice — domain seating outcomes."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

REPORT = Path("/output/time-seat.json")
SEAT = Path("/app/ops/run_time_seat.sh")
BAND_LO, BAND_HI = 1, 2
DATA_SOURCES = Path("/app/data/sources")
DIGEST_LEDGER = Path("/app/data/sources.sha256")
OPS = Path("/var/lib/time/ops")
ETC_SRC = Path("/etc/chrony/sources.d")
TMPL = Path("/app/config/chrony/sources.d")


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=check,
        text=True,
        capture_output=True,
    )


def _parse_list(path: Path, key: str) -> list[str]:
    text = path.read_text()
    m = re.search(rf"{key}\s*=\s*\[([^\]]*)\]", text)
    if not m:
        return []
    return [x.strip().strip('"').strip("'") for x in m.group(1).split(",") if x.strip()]


def _stratum_from_template(name: str) -> int:
    short = name.removeprefix("pool-")
    text = (TMPL / f"{short}.sources").read_text()
    m = re.search(r"stratum\s+(\d+)", text)
    assert m, f"missing stratum comment for {name}"
    return int(m.group(1))


def _authority_field(key: str) -> str:
    for line in (OPS / "authority.toml").read_text().splitlines():
        if line.startswith(key) and not line.startswith("surface_"):
            return line.split("=", 1)[1].strip().strip('"')
    raise AssertionError(f"missing {key} in authority.toml")


def _offsets() -> dict[str, float]:
    out: dict[str, float] = {}
    for line in (OPS / "offsets.toml").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = float(v.strip())
    return out


def _expected_matrix() -> tuple[list[dict], set[str]]:
    roster = _parse_list(OPS / "roster.toml", "members")
    held = set(_parse_list(OPS / "holds.toml", "held"))
    selected: set[str] = set()
    rows: list[dict] = []
    for name in roster:
        stratum = _stratum_from_template(name)
        is_hold = name in held
        is_sel = (
            name in roster
            and BAND_LO <= stratum <= BAND_HI
            and not is_hold
        )
        if is_sel:
            selected.add(name)
        rows.append(
            {
                "name": name,
                "stratum": stratum,
                "selected": is_sel,
                "hold": is_hold,
            }
        )
    return rows, selected


def _load_report() -> dict:
    assert REPORT.is_file(), "missing /output/time-seat.json"
    return json.loads(REPORT.read_text())


def _folded_ntp() -> str:
    p = OPS / "ntp.folded"
    assert p.is_file(), "missing folded NTP state"
    raw = p.read_text().strip()
    return raw.removeprefix("NTP=")


@pytest.fixture(scope="module", autouse=True)
def _seat_once() -> None:
    """Ensure stock seating entrypoint has been invoked before module tests."""
    if not REPORT.is_file():
        _run(["bash", str(SEAT)], check=True)


def test_q3_opal() -> None:
    """Report exposes required seating fields and types."""
    doc = _load_report()
    assert isinstance(doc.get("schema_tag"), str) and doc["schema_tag"]
    assert isinstance(doc.get("preference"), str)
    assert isinstance(doc.get("sync_ok"), bool)
    assert isinstance(doc.get("offset_bound_ms"), (int, float))
    sources = doc.get("sources")
    assert isinstance(sources, list) and sources
    for row in sources:
        assert set(row) >= {"name", "stratum", "selected", "hold"}
        assert isinstance(row["name"], str)
        assert isinstance(row["stratum"], int)
        assert isinstance(row["selected"], bool)
        assert isinstance(row["hold"], bool)


def test_n7_topaz() -> None:
    """Preference mode is durable or authority in report and prefer.toml."""
    doc = _load_report()
    contract = Path("/app/docs/seating_contract.md").read_text()
    allowed = set(re.findall(r"`(durable|authority)`", contract))
    assert allowed, "graded preference modes missing from seating contract"
    assert doc["preference"] in allowed
    mode = (OPS / "prefer.toml").read_text()
    assert any(
        re.search(rf'mode\s*=\s*"{m}"', mode) for m in allowed
    )


def test_k4_beryl() -> None:
    """Selected set equals roster intersect band intersect not-held."""
    doc = _load_report()
    expected, selected = _expected_matrix()
    by_name = {r["name"]: r for r in doc["sources"]}
    for row in expected:
        got = by_name[row["name"]]
        assert got["stratum"] == row["stratum"]
        assert got["selected"] is row["selected"]
        assert got["hold"] is row["hold"]
    assert {r["name"] for r in doc["sources"] if r["selected"]} == selected
    assert selected == _expected_matrix()[1]


def test_m2_garnet() -> None:
    """Held roster peers appear with hold true and selected false."""
    doc = _load_report()
    held_rows = [r for r in doc["sources"] if r["hold"]]
    assert held_rows, "held roster peers must appear in sources"
    expected_held = set(_parse_list(OPS / "holds.toml", "held"))
    for row in held_rows:
        assert not row["selected"]
        assert row["name"] in expected_held


def test_r6_quartz() -> None:
    """sync_ok requires live chrony and folded NTP to match selection."""
    doc = _load_report()
    _, selected = _expected_matrix()
    live = {"pool-" + p.stem for p in ETC_SRC.glob("*.sources")}
    assert live == selected
    assert _folded_ntp() == _authority_field("primary_ntp")
    assert doc["sync_ok"]


def test_w8_zircon() -> None:
    """offset_bound_ms matches durable budget for the selected peer."""
    doc = _load_report()
    _, selected = _expected_matrix()
    assert selected == _expected_matrix()[1]
    sole = next(iter(selected))
    assert float(doc["offset_bound_ms"]) == pytest.approx(_offsets()[sole])
    # Must not equal the optimistic surface figure baked into the broken path.
    assert float(doc["offset_bound_ms"]) != pytest.approx(0.5)


def test_j1_jasper() -> None:
    """schema_tag matches durable authority, not the surface tag."""
    doc = _load_report()
    assert doc["schema_tag"] == _authority_field("schema_tag")
    assert doc["schema_tag"] != "time.seat.v1"


def test_p5_peridot() -> None:
    """Live chrony sources.d seats only the selected peer."""
    _, selected = _expected_matrix()
    live_files = sorted(p.name for p in ETC_SRC.glob("*.sources"))
    expect_files = sorted(n.removeprefix("pool-") + ".sources" for n in selected)
    assert live_files == expect_files
    text = (ETC_SRC / "alpha.sources").read_text()
    primary = _authority_field("primary_ntp")
    decoy = Path("/etc/systemd/timesyncd.conf.d/40-lab.conf").read_text()
    decoy_ntp = next(
        ln.split("=", 1)[1].strip()
        for ln in decoy.splitlines()
        if ln.startswith("NTP=")
    )
    assert primary in text
    assert decoy_ntp not in text


def test_v9_spinel() -> None:
    """Lexical timesync fold yields durable primary NTP, not decoy."""
    primary = _authority_field("primary_ntp")
    assert _folded_ntp() == primary
    dropins = Path("/etc/systemd/timesyncd.conf.d")
    assert (dropins / "40-lab.conf").is_file()
    lab = (dropins / "40-lab.conf").read_text()
    local = (dropins / "90-local.conf").read_text()
    assert "NTP=" in lab and primary not in lab
    assert primary in local


def test_t2_tourmaline() -> None:
    """Two seating runs produce byte-identical JSON."""
    first = REPORT.read_bytes()
    _run(["bash", str(SEAT)], check=True)
    second = REPORT.read_bytes()
    assert first == second


def test_h5_hematite() -> None:
    """Wiping output and re-entering the stock entrypoint restores outcomes."""
    before = _load_report()
    REPORT.unlink()
    assert not REPORT.exists()
    _run(["bash", str(SEAT)], check=True)
    after = _load_report()
    assert after["schema_tag"] == before["schema_tag"]
    assert after["preference"] == before["preference"]
    assert after["sync_ok"]
    assert {r["name"] for r in after["sources"] if r["selected"]} == _expected_matrix()[1]


def test_u4_onyx() -> None:
    """Frozen samples under /app/data/sources keep packaging digests."""
    proc = _run(["sha256sum", "-c", str(DIGEST_LEDGER)], check=False)
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_y6_amber() -> None:
    """timehealth can look synchronized while seating still must be durable-correct."""
    health = _run(["/usr/local/bin/timehealth"], check=False)
    assert health.returncode == 0
    assert re.search(r"synchronis", health.stdout, re.IGNORECASE)
    doc = _load_report()
    # Surface green must coexist with durable seating truth — not replace it.
    assert doc["sync_ok"]
    assert {r["name"] for r in doc["sources"] if r["selected"]} == {
        next(iter(_expected_matrix()[1]))
    }
    sole = next(iter(_expected_matrix()[1]))
    assert float(doc["offset_bound_ms"]) == pytest.approx(_offsets()[sole])


def test_c8_citrine() -> None:
    """Out-of-band roster peers are never selected."""
    doc = _load_report()
    by_name = {r["name"]: r for r in doc["sources"]}
    for name in ("pool-beta", "pool-epsilon"):
        assert name in by_name
        assert not by_name[name]["selected"]
        stratum = by_name[name]["stratum"]
        assert stratum < BAND_LO or stratum > BAND_HI
