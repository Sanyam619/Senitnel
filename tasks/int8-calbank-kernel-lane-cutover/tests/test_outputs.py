"""Outcome checks for INT8 cal-bank × kernel-lane cutover."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

LEDGER = Path("/output/eval-ledger.json")
SURFACE = Path("/app/data/fixtures/surface_ok.json")
SEED = Path("/app/data/fixtures/seed.json")
DURABLE = Path("/app/data/banks/tip_durable.json")
LIVE = Path("/app/data/banks/tip_live.json")
ACTIVE = Path("/app/data/banks/scales_active.bin")
E7 = Path("/app/data/banks/scales_e7.bin")
RESUME = Path("/app/data/checkpoints/resume_pack.json")
SCENARIOS = Path("/app/data/eval/scenarios.json")
PROFILES = Path("/app/config/profiles")
RUNTIME_TOML = Path("/app/config/runtime.toml")
STAMP = Path("/app/data/checkpoints/rebase.stamp")

EXPECTED_TOP1 = {
    "cold_a": 0.91,
    "resume_a": 0.91,
    "cold_b": 0.87,
    "resume_b": 0.87,
    "mix_c": 0.84,
    "mix_d": 0.89,
}

EXPECTED_LANE = {
    "cold_a": "k1",
    "resume_a": "k1",
    "cold_b": "k0",
    "resume_b": "k0",
    "mix_c": "k2",
    "mix_d": "k1",
}

EXPECTED_MODE = {
    "cold_a": "int8",
    "resume_a": "int8",
    "cold_b": "int8",
    "resume_b": "int8",
    "mix_c": "mixed",
    "mix_d": "int8",
}


def _load(path: Path = LEDGER) -> dict:
    assert path.is_file(), f"missing {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def _by_id(payload: dict) -> dict[str, dict]:
    rows = payload.get("scenarios")
    assert isinstance(rows, list) and rows, "scenarios must be a non-empty list"
    out = {}
    for row in rows:
        assert isinstance(row, dict)
        assert "id" in row
        out[row["id"]] = row
    return out


def _run_eval() -> None:
    proc = subprocess.run(
        ["/app/eval/run_eval.sh"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def _gen_floor() -> int:
    text = RUNTIME_TOML.read_text(encoding="utf-8")
    in_codec = False
    floor = 2
    for line in text.splitlines():
        t = line.strip()
        if t.startswith("["):
            in_codec = t == "[codec]"
            continue
        if in_codec and t.startswith("gen_floor"):
            rest = t.split("=", 1)[-1].strip()
            floor = int(rest)
    return floor


def _codec_hot() -> bool:
    hot = 0
    gen = 0
    paths = sorted(
        p for p in PROFILES.glob("*.toml") if p.name[:2].isdigit() and p.name[2:3] == "-"
    )
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            t = line.strip()
            if t.startswith("hot"):
                rest = t.split("=", 1)[-1].strip()
                if rest in {"1", "true"}:
                    hot = 1
                elif rest in {"0", "false"}:
                    hot = 0
            if t.startswith("gen"):
                rest = t.split("=", 1)[-1].strip()
                if rest.isdigit():
                    gen = int(rest)
    return hot == 1 and gen >= _gen_floor()


def _score(blob: bytes, epoch: int, lane: int, mixed: int, salt: int) -> float:
    if blob[0] != (epoch & 0xFF):
        return 0.49 + 0.01 * (salt % 9) + 0.004 * lane
    idx = 1 + (salt % 32)
    acc = (blob[idx] + 40 + 3 * lane) / 100.0
    if mixed:
        acc -= 0.05
    return max(0.01, min(0.99, acc))


def _independent_rows() -> dict[str, dict]:
    durable = json.loads(DURABLE.read_text(encoding="utf-8"))
    live = json.loads(LIVE.read_text(encoding="utf-8"))
    assert durable.get("sealed") is True
    bound = durable["epoch"]
    assert bound != live["epoch"]
    pack = json.loads(RESUME.read_text(encoding="utf-8"))
    assert STAMP.is_file()
    assert pack.get("epoch") == bound
    blob = ACTIVE.read_bytes()
    assert blob[0] == bound
    hot = _codec_hot()
    out = {}
    for sc in json.loads(SCENARIOS.read_text(encoding="utf-8")):
        mask = sc["mask"] if hot else [0] * len(sc["mask"])
        lane_idx = sc["fallback"]
        for i, m in enumerate(mask):
            if m != 0:
                lane_idx = i
                break
        any_live = any(m != 0 for m in mask)
        mixed = 1 if (not any_live and lane_idx == sc["fallback"]) else 0
        epoch = bound
        top1 = _score(blob, epoch, lane_idx, mixed, sc["salt"])
        out[sc["id"]] = {
            "lane": f"k{lane_idx}",
            "mode": "mixed" if mixed else "int8",
            "top1": top1,
        }
    return out


def test_bank_epoch_binds_durable_tip():
    """bank_epoch must equal sealed durable tip, not live tip."""
    durable = json.loads(DURABLE.read_text(encoding="utf-8"))
    live = json.loads(LIVE.read_text(encoding="utf-8"))
    payload = _load()
    assert payload.get("version") == 1
    assert payload.get("bank_epoch") == durable["epoch"]
    assert payload.get("bank_epoch") != live["epoch"]
    assert durable.get("sealed") is True


def test_lane_matrix_follows_live_mask():
    """Lane matrix must match live-mask / fallback cutover outcomes."""
    by_id = _by_id(_load())
    for sid, lane in EXPECTED_LANE.items():
        assert sid in by_id, sid
        assert by_id[sid].get("lane") == lane, (sid, by_id[sid])


def test_resume_top1_matches_cold():
    """Resume top1 must match cold-start for paired scenarios."""
    by_id = _by_id(_load())
    assert by_id["cold_a"]["top1"] == by_id["resume_a"]["top1"]
    assert by_id["cold_b"]["top1"] == by_id["resume_b"]["top1"]
    assert abs(float(by_id["cold_a"]["top1"]) - EXPECTED_TOP1["cold_a"]) < 1e-9
    assert abs(float(by_id["cold_b"]["top1"]) - EXPECTED_TOP1["cold_b"]) < 1e-9


def test_graded_top1_values():
    """Graded top1 values must match verifier-owned EXPECTED."""
    by_id = _by_id(_load())
    for sid, want in EXPECTED_TOP1.items():
        got = float(by_id[sid]["top1"])
        assert abs(got - want) < 1e-9, (sid, got, want)


def test_mode_int8_vs_mixed():
    """Mode field must reflect int8 vs mixed-precision fallback."""
    by_id = _by_id(_load())
    for sid, mode in EXPECTED_MODE.items():
        assert by_id[sid].get("mode") == mode, (sid, by_id[sid])


def test_deep_disagrees_with_surface():
    """Deep ledger must disagree with surface_ok on at least one shared top1."""
    deep = _by_id(_load())
    surface = _by_id(json.loads(SURFACE.read_text(encoding="utf-8")))
    disagreed = 0
    for sid in EXPECTED_TOP1:
        assert sid in surface
        if abs(float(deep[sid]["top1"]) - float(surface[sid]["top1"])) > 1e-9:
            disagreed += 1
    assert disagreed >= 1


def test_fixtures_seed_intact():
    """Fixtures seed must stay intact; ledger schema remains versioned."""
    payload = _load()
    assert payload.get("version") == 1
    assert isinstance(payload.get("scenarios"), list)
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    assert seed.get("anchor") == "do-not-modify"
    assert seed.get("seed") == "int8-calbank-v1"


def test_rematerialize_stable_after_poison():
    """Re-running deep eval rematerializes tips and keeps the ledger stable."""
    LIVE.write_text(
        '{\n  "epoch": 99,\n  "sealed": false,\n  "label": "poison"\n}\n',
        encoding="utf-8",
    )
    first = LEDGER.read_bytes()
    _run_eval()
    second = LEDGER.read_bytes()
    assert first == second
    live = json.loads(LIVE.read_text(encoding="utf-8"))
    assert live.get("epoch") != 99
    assert _load().get("bank_epoch") == 7
    by_id = _by_id(_load())
    for sid, want in EXPECTED_TOP1.items():
        assert abs(float(by_id[sid]["top1"]) - want) < 1e-9, (sid, by_id[sid])


def test_ledger_matches_independent_reconstruction():
    """Ledger rows must match an independent tip/codec/scale reconstruction."""
    _run_eval()
    by_id = _by_id(_load())
    indep = _independent_rows()
    for sid, want in indep.items():
        got = by_id[sid]
        assert got.get("lane") == want["lane"], (sid, got, want)
        assert got.get("mode") == want["mode"], (sid, got, want)
        assert abs(float(got["top1"]) - float(want["top1"])) < 1e-9, (sid, got, want)
    assert ACTIVE.read_bytes()[0] == E7.read_bytes()[0]
    assert json.loads(RESUME.read_text(encoding="utf-8")).get("epoch") == 7
