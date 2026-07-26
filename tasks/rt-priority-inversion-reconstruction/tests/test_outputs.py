"""Verifier for kernlab analysis outputs."""

import ast
import json
import subprocess

import pytest
from pathlib import Path

OUT = Path("/output/analysis.json")
MANIFEST = Path("/opt/kernlab/config/manifest.txt")
PROBE = Path("/opt/kernlab/bin/kernprobe")
REF = Path(__file__).resolve().parent / "chain_ref.py"


def _load_cases():
    mod = ast.parse(REF.read_text(encoding="utf-8"))
    for node in mod.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "CASES":
                    return ast.literal_eval(node.value)
    raise RuntimeError("CASES missing from chain_ref.py")


CASES = _load_cases()


def _scenario_ids():
    rows = []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 1:
            rows.append(parts[0])
    return rows


SCENARIOS = _scenario_ids()


def _load_doc():
    assert OUT.is_file(), f"missing {OUT}"
    doc = json.loads(OUT.read_text(encoding="utf-8"))
    assert doc.get("version") == 1
    assert isinstance(doc.get("scenarios"), dict)
    return doc


def _replay(sid: str) -> int:
    _load_doc()
    proc = subprocess.run(
        [
            "/opt/kernlab/bin/klreplay",
            "--cfg",
            f"/opt/kernlab/config/{sid}.toml",
            "--trace",
            f"/opt/kernlab/traces/{sid}.evt",
            "--analysis",
            str(OUT),
            "--scenario",
            sid,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return 1
    row = json.loads(proc.stdout.strip())
    return int(row.get("misses", 1))


def test_probe_regenerates_analysis():
    """kernprobe must rebuild analysis.json from the compiled probe binary."""
    assert PROBE.is_file(), f"missing {PROBE}"
    if OUT.exists():
        OUT.unlink()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [
            str(PROBE),
            "--manifest",
            str(MANIFEST),
            "--out",
            str(OUT),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    doc = _load_doc()
    for sid in SCENARIOS:
        assert sid in doc["scenarios"]


def test_h4_schema_bundle():
    """analysis.json exposes version and every manifest scenario."""
    doc = _load_doc()
    for sid in SCENARIOS:
        assert sid in doc["scenarios"]
        row = doc["scenarios"][sid]
        assert isinstance(row.get("missed_deadline_task"), str)
        assert isinstance(row.get("chain"), list)
        assert len(row["chain"]) == 3
        assert isinstance(row.get("ceilings"), dict)


@pytest.mark.parametrize("sid", sorted(CASES.keys()))
def test_chain_matches_reference(sid):
    """Each manifest row reports the expected blocking band."""
    doc = _load_doc()
    want = CASES[sid]
    row = doc["scenarios"][sid]
    assert row["missed_deadline_task"] == want["missed"]
    assert row["chain"] == want["chain"]
    assert row["ceilings"] == want["ceilings"]


@pytest.mark.parametrize("sid", sorted(CASES.keys()))
def test_replay_zero_misses(sid):
    """Submitted ceilings pass deterministic replay proof."""
    assert _replay(sid) == 0
