"""Verifier for wiretap forensic outputs."""

import json
import subprocess
from pathlib import Path

OUT = Path("/output")
REASM = OUT / "reassembled"
FINDINGS = OUT / "findings.json"
MANIFEST = Path("/opt/wiretap/data/manifest.json")

EXPECTED = json.loads('{\n    "flow_alfa": [\n        "a33c0aef4c36c550886cc95f20c1de28aaa6e2a84323411570f91581e70acd9d",\n        "df5435bd2ef85d0750d86ffdadd527e4dfa5bb74de8915709fc0ed18575c4299",\n        22,\n        19,\n        [],\n        [],\n        [\n            0,\n            1,\n            2,\n            3,\n            4,\n            5,\n            6,\n            7,\n            8,\n            9\n        ]\n    ],\n    "flow_bravo": [\n        "1c5dc93d56d6438e3231071d8c29055d32ba9a747822ccd5c6b2247adc1af350",\n        "6cab76e227d9d7963c7ab1d4c9bd1983bcc01df9b39e4045683e789c4c63b52f",\n        38,\n        27,\n        [\n            [\n                19,\n                20\n            ],\n            [\n                20,\n                21\n            ],\n            [\n                21,\n                22\n            ],\n            [\n                22,\n                23\n            ],\n            [\n                23,\n                24\n            ],\n            [\n                24,\n                25\n            ]\n        ],\n        [],\n        []\n    ],\n    "flow_charlie": [\n        "d0d97c504e6761b21551d895680dfa816b7c23fbe1b86a749c3bcf020afe9cd4",\n        "16fa987bb28defdffb326cf5874ccd92cb4c1eb785f830e58e75a48b1405a63d",\n        25,\n        26,\n        [],\n        [],\n        []\n    ],\n    "flow_delta": [\n        "c7750381ff513d91f2199e10a7ee47b8f78fe7cb5c52b6f398201397b72b4a9e",\n        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",\n        24,\n        0,\n        [],\n        [],\n        []\n    ]\n}')

SHA_C2S = 0
SHA_S2C = 1
LEN_C2S = 2
LEN_S2C = 3
INJ_C2S = 4
INJ_S2C = 5
OVL_C2S = 6


def _flow_ids() -> list[str]:
    mf = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [row["id"] for row in mf["flows"]]


FLOWS = _flow_ids()


def _sha256(data: bytes) -> str:
    proc = subprocess.run(
        ["sha256sum"],
        input=data,
        capture_output=True,
        check=True,
    )
    return proc.stdout.decode().split()[0]


def _load_findings() -> dict:
    assert FINDINGS.is_file(), f"missing {FINDINGS}"
    doc = json.loads(FINDINGS.read_text(encoding="utf-8"))
    assert doc.get("version") == 1
    assert isinstance(doc.get("flows"), dict)
    return doc


def _covered_positions(ranges):
    pos = set()
    for start, end in ranges:
        for i in range(int(start), int(end)):
            pos.add(i)
    return pos


def _overlap_rel_offs(notes, direction):
    return {n.get("rel_off") for n in notes if n.get("dir") == direction and n.get("rel_off") is not None}


def test_binary_rebuilt():
    """wiretap analyze runs successfully after agent rebuild."""
    result = subprocess.run(
        [
            "/opt/wiretap/bin/wiretap",
            "analyze",
            "--manifest",
            str(MANIFEST),
            "--out",
            "/tmp/verify_out",
        ],
        capture_output=True,
    )
    assert result.returncode == 0


def test_n2_all_flow_artifacts_exist():
    """Each manifest flow emits lane binaries and a findings row."""
    doc = _load_findings()
    for fid in FLOWS:
        exp = EXPECTED[fid]
        c2s = REASM / f"{fid}_c2s.bin"
        s2c = REASM / f"{fid}_s2c.bin"
        assert c2s.is_file()
        assert s2c.is_file()
        if exp[LEN_C2S] > 0:
            assert c2s.stat().st_size > 0
        if exp[LEN_S2C] > 0:
            assert s2c.stat().st_size > 0
        assert fid in doc["flows"]


def test_u1_alfa_c2s_bytes():
    """flow_alfa client lane bytes match reconciled delivery."""
    fid = "flow_alfa"
    want = EXPECTED[fid][SHA_C2S]
    path = REASM / f"{fid}_c2s.bin"
    assert path.is_file()
    assert _sha256(path.read_bytes()) == want


def test_k3_alfa_s2c_bytes():
    """flow_alfa server lane bytes match reconciled delivery."""
    fid = "flow_alfa"
    want = EXPECTED[fid][SHA_S2C]
    path = REASM / f"{fid}_s2c.bin"
    assert path.is_file()
    assert _sha256(path.read_bytes()) == want
    doc = _load_findings()
    assert doc["flows"][fid]["s2c_len"] == path.stat().st_size


def test_m8_bravo_c2s_keeps_first():
    """flow_bravo client lane resists tampered resend bytes."""
    fid = "flow_bravo"
    want = EXPECTED[fid][SHA_C2S]
    path = REASM / f"{fid}_c2s.bin"
    assert _sha256(path.read_bytes()) == want


def test_p2_bravo_injected_ranges():
    """flow_bravo contested offsets match reconciled byte positions."""
    fid = "flow_bravo"
    exp = EXPECTED[fid]
    doc = _load_findings()
    got = doc["flows"][fid]["c2s_injected"]
    want = exp[INJ_C2S]
    assert len(got) > 0
    assert _covered_positions(got) == _covered_positions(want)


def test_q5_charlie_s2c_gap():
    """flow_charlie server lane waits for a late middle slice."""
    fid = "flow_charlie"
    want = EXPECTED[fid][SHA_S2C]
    path = REASM / f"{fid}_s2c.bin"
    assert _sha256(path.read_bytes()) == want
    doc = _load_findings()
    assert doc["flows"][fid]["s2c_len"] == EXPECTED[fid][LEN_S2C]


def test_r7_delta_c2s_window():
    """flow_delta client lane honors post-shrink accept window."""
    fid = "flow_delta"
    want = EXPECTED[fid][SHA_C2S]
    path = REASM / f"{fid}_c2s.bin"
    assert _sha256(path.read_bytes()) == want
    doc = _load_findings()
    assert doc["flows"][fid]["c2s_len"] == EXPECTED[fid][LEN_C2S]


def test_s4_findings_schema():
    """findings.json exposes required per-flow forensic fields."""
    doc = _load_findings()
    for fid in FLOWS:
        row = doc["flows"][fid]
        assert isinstance(row["c2s_len"], int)
        assert isinstance(row["s2c_len"], int)
        assert isinstance(row["c2s_injected"], list)
        assert isinstance(row["s2c_injected"], list)
        assert isinstance(row["overlap_notes"], list)
    assert len(doc["flows"]["flow_bravo"]["c2s_injected"]) > 0


def test_v4_s2c_injected_values():
    """each flow reports reconciled server-lane contested offsets."""
    doc = _load_findings()
    for fid in FLOWS:
        exp = EXPECTED[fid]
        got = doc["flows"][fid]["s2c_injected"]
        want = exp[INJ_S2C]
        assert _covered_positions(got) == _covered_positions(want)


def test_w6_reported_lengths_match_bins():
    """findings.json length fields match emitted binary sizes and contested catalog."""
    doc = _load_findings()
    for fid in FLOWS:
        row = doc["flows"][fid]
        assert row["c2s_len"] == (REASM / f"{fid}_c2s.bin").stat().st_size
        assert row["s2c_len"] == (REASM / f"{fid}_s2c.bin").stat().st_size
    bravo_inj = doc["flows"]["flow_bravo"]["c2s_injected"]
    assert isinstance(bravo_inj, list) and len(bravo_inj) > 0


def test_t9_overlap_notes_alfa():
    """flow_alfa records overlap resolution offsets on the client lane."""
    doc = _load_findings()
    got = doc["flows"]["flow_alfa"]["overlap_notes"]
    want_offs = set(EXPECTED["flow_alfa"][OVL_C2S])
    got_offs = _overlap_rel_offs(got, "c2s")
    assert got_offs == want_offs


def test_h2_overlap_kept_alfa():
    """flow_alfa overlap notes name which duplicate copy was kept."""
    doc = _load_findings()
    notes = [
        n
        for n in doc["flows"]["flow_alfa"]["overlap_notes"]
        if n.get("dir") == "c2s" and n.get("rel_off") is not None
    ]
    assert notes
    for note in notes:
        assert note.get("kept") == "later"
