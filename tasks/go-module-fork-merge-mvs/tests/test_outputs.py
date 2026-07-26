"""Verifier tests for the go module fork-merge CI matrix task."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

MATRIXCI = "/app/bin/matrixci"
REPO = Path("/app/src")
DOCS = Path("/app/docs")
PROXY = Path("/app/proxy")
REPORT = Path("/output/build-matrix.json")

LEDGERS = Path("/tests/ledgers")
PROXY_LEDGER = LEDGERS / "proxy.sha256"
POLICY_LEDGER = LEDGERS / "policy.sha256"

FLOORS = {
    "example.org/logstream": "v1.4.0",
    "example.org/httpmux": "v0.5.2",
    "example.org/toolchain": "v0.9.0",
}
CAPS = {
    "example.org/logstream": "v1.4.9",
    "example.org/httpmux": "v0.5.9",
    "example.org/toolchain": "v0.9.9",
}
REQUIRED_EXCLUDES = [
    ("example.org/toolchain", "v0.9.0"),
    ("example.org/logstream", "v1.4.2"),
]
PROHIBITED_REPLACE_TARGETS = {
    "internal.example/platform",
    "example.org/serde",
}
RETRACT_RANGES = {
    "example.org/logstream": [("v1.4.1", "v1.4.2")],
}
EXPECTED_SELECTED = {
    "example.org/logstream": "v1.4.3",
    "example.org/httpmux": "v0.5.4",
    "example.org/toolchain": "v0.9.5",
}


def _parse_version(v: str) -> tuple[int, ...]:
    core = v.split("+", 1)[0]
    if core.startswith("v"):
        core = core[1:]
    parts = core.split(".")
    return tuple(int(p) if p.isdigit() else 0 for p in parts)


def _ge(a: str, b: str) -> bool:
    return _parse_version(a) >= _parse_version(b)


def _le(a: str, b: str) -> bool:
    return _parse_version(a) <= _parse_version(b)


def _assert_ledger(ledger: Path, root: Path) -> None:
    assert ledger.is_file(), f"missing ledger {ledger}"
    result = subprocess.run(
        ["sha256sum", "-c", str(ledger)],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"ledger drift under {root}:\n{result.stdout}\n{result.stderr}"
        )


def _assert_fixture_bytes_intact() -> None:
    _assert_ledger(PROXY_LEDGER, PROXY)
    _assert_ledger(POLICY_LEDGER, DOCS)


def _fresh_report(out_path: Path) -> dict:
    _assert_fixture_bytes_intact()
    subprocess.run(
        [MATRIXCI, "report", "--out", str(out_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(out_path.read_text())


def _submitted() -> dict:
    assert REPORT.is_file(), f"missing submitted report at {REPORT}"
    data = json.loads(REPORT.read_text())
    assert "toolchains" in data
    return data


def _read_gomod(path: Path) -> str:
    assert path.is_file(), f"missing {path}"
    return path.read_text()


def _extract_exclude_lines(gomod_text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    lines = gomod_text.splitlines()
    in_block = False
    for raw in lines:
        line = raw.split("//", 1)[0].strip()
        if not line:
            continue
        if in_block:
            if line == ")":
                in_block = False
                continue
            parts = line.split()
            if len(parts) >= 2:
                out.append((parts[0], parts[1]))
            continue
        if line == "exclude (":
            in_block = True
            continue
        if line.startswith("exclude "):
            body = line[len("exclude "):].strip()
            parts = body.split()
            if len(parts) >= 2:
                out.append((parts[0], parts[1]))
    return out


def _extract_replace_directives(gomod_text: str) -> list[tuple[str, str, str, str]]:
    """Return (old_path, old_ver_or_empty, new_path, new_ver) for every replace."""
    out: list[tuple[str, str, str, str]] = []
    lines = gomod_text.splitlines()
    in_block = False
    for raw in lines:
        line = raw.split("//", 1)[0].strip()
        if not line:
            continue
        body = None
        if in_block:
            if line == ")":
                in_block = False
                continue
            body = line
        elif line == "replace (":
            in_block = True
            continue
        elif line.startswith("replace "):
            body = line[len("replace "):].strip()
        if body is None or "=>" not in body:
            continue
        left, right = body.split("=>", 1)
        lp = left.strip().split()
        rp = right.strip().split()
        if not lp or not rp:
            continue
        old_path = lp[0]
        old_ver = lp[1] if len(lp) > 1 else ""
        new_path = rp[0]
        new_ver = rp[1] if len(rp) > 1 else ""
        out.append((old_path, old_ver, new_path, new_ver))
    return out


def test_report_written_and_matrix_clean():
    """Submitted report exists and a fresh matrixci run lands every cell at ok."""
    submitted = _submitted()
    assert "toolchains" in json.loads(REPORT.read_text())
    assert submitted["toolchains"]
    data = _fresh_report(Path("/tmp/matrix-cells.json"))
    assert set(data["toolchains"]) == {"go1.22", "go1.23"}
    for prof in ("go1.22", "go1.23"):
        assert set(data["toolchains"][prof]) == {"mod", "vendor"}
        for mode in ("mod", "vendor"):
            cell = data["toolchains"][prof][mode]
            assert cell["status"] == "ok", (
                f"{prof}/{mode}: {cell['status']} :: {cell.get('diagnostics')}"
            )
            assert cell["diagnostics"] == []
            if mode == "vendor":
                assert cell["vendor_ledger_agrees"] is True


def test_policy_rollups_clean():
    """Policy rollups that the harness exposes are all respected / empty."""
    data = _fresh_report(Path("/tmp/matrix-rollups.json"))
    assert data["replace_conflicts"] == [], data["replace_conflicts"]
    assert data["vendor_incompatible_drift"] == [], data["vendor_incompatible_drift"]
    assert data["retract"]["avoided"] is True, data["retract"]
    assert data["cve_floor"]["respected"] is True, data["cve_floor"]
    assert data["required_excludes"]["respected"] is True, data["required_excludes"]
    assert data["prohibited_replaces"]["respected"] is True, data["prohibited_replaces"]
    assert data["retained_forks"]["respected"] is True, data["retained_forks"]


def test_prohibited_replaces_absent_in_source():
    """Neither go.mod may replace a module the policy forbids replacing."""
    for label, path in (("root", REPO / "go.mod"), ("sub", REPO / "svc" / "go.mod")):
        text = _read_gomod(path)
        for old_path, _, _, _ in _extract_replace_directives(text):
            assert old_path not in PROHIBITED_REPLACE_TARGETS, (
                f"{label} go.mod replaces prohibited module {old_path}"
            )


def test_root_gomod_declares_required_excludes():
    """Required excludes must be declared in the root go.mod (sub alone is not enough)."""
    text = _read_gomod(REPO / "go.mod")
    declared = set(_extract_exclude_lines(text))
    for mod, ver in REQUIRED_EXCLUDES:
        assert (mod, ver) in declared, (
            f"root go.mod is missing required exclude directive: {mod} {ver}"
        )


def test_guarded_module_selections():
    """Windowed modules resolve to the unique in-window, non-retracted, non-excluded pins."""
    data = _fresh_report(Path("/tmp/matrix-selected.json"))
    for prof in ("go1.22", "go1.23"):
        for mode in ("mod", "vendor"):
            selected = data["toolchains"][prof][mode]["selected"]
            for mod, expect in EXPECTED_SELECTED.items():
                assert selected[mod] == expect, (
                    f"{prof}/{mode} {mod}: got {selected[mod]}, want {expect}"
                )
            ver = selected["example.org/logstream"]
            assert _ge(ver, FLOORS["example.org/logstream"])
            assert _le(ver, CAPS["example.org/logstream"])
            for low, high in RETRACT_RANGES["example.org/logstream"]:
                assert not (_ge(ver, low) and _le(ver, high)), ver
            assert selected["example.org/toolchain"] != "v0.9.0"


def test_unversioned_retained_httpmux_fork():
    """Both trees keep an unversioned httpmux => httpmux-fork replace at the policy min."""
    data = _fresh_report(Path("/tmp/matrix-httpmux.json"))
    both = {
        (prof, mode): data["toolchains"][prof][mode]["selected"]["example.org/httpmux"]
        for prof in ("go1.22", "go1.23")
        for mode in ("mod", "vendor")
    }
    assert set(both.values()) == {"v0.5.4"}, both
    for label, path in (("root", REPO / "go.mod"), ("sub", REPO / "svc" / "go.mod")):
        reps = _extract_replace_directives(_read_gomod(path))
        httpmux = [r for r in reps if r[0] == "example.org/httpmux"]
        assert httpmux, f"{label} go.mod missing httpmux replace"
        unversioned = [r for r in httpmux if r[1] == ""]
        assert unversioned, (
            f"{label} go.mod httpmux replace must be unversioned on the LHS, got {httpmux}"
        )
        assert unversioned[0][2] == "example.org/httpmux-fork"
        assert _ge(unversioned[0][3], "v0.5.4"), unversioned[0]


def test_cross_toolchain_selection_invariant():
    """Every module's selected version is identical across both toolchain profiles."""
    data = _fresh_report(Path("/tmp/matrix-invariant.json"))
    for mode in ("mod", "vendor"):
        s22 = data["toolchains"]["go1.22"][mode]["selected"]
        s23 = data["toolchains"]["go1.23"][mode]["selected"]
        assert s22 == s23, f"{mode}: go1.22 selects {s22} vs go1.23 selects {s23}"


def test_serde_incompatible_in_selection_and_vendor():
    """Serde carries +incompatible in both the selection and the vendor ledger."""
    data = _fresh_report(Path("/tmp/matrix-serde.json"))
    ver = data["toolchains"]["go1.23"]["mod"]["selected"]["example.org/serde"]
    assert ver.endswith("+incompatible"), ver
    modules_txt = (REPO / "bnd" / "modules.txt").read_text()
    assert re.search(
        r"^# example\.org/serde v2\.0\.0\+incompatible\s*$",
        modules_txt,
        re.MULTILINE,
    ), modules_txt


def test_vendor_go_directive_matches_effective_fork():
    """Vendor httpmux entry retains the fork replace and the fork's go directive."""
    modules_txt = (REPO / "bnd" / "modules.txt").read_text()
    m = re.search(
        r"^# example\.org/httpmux .* => example\.org/httpmux-fork v0\.5\.4\n(## .*)$",
        modules_txt,
        re.MULTILINE,
    )
    assert m is not None, "vendor entry for httpmux fork v0.5.4 not found"
    assert "go 1.23" in m.group(1), m.group(1)
    data = _fresh_report(Path("/tmp/matrix-godir.json"))
    assert data["vendor_incompatible_drift"] == [], data["vendor_incompatible_drift"]
    assert data["retained_forks"]["respected"] is True
    for prof in ("go1.22", "go1.23"):
        for mode in ("mod", "vendor"):
            cell = data["toolchains"][prof][mode]
            assert cell["status"] == "ok", (prof, mode, cell)


def test_tools_import_is_build_guarded():
    """tools.go must be build-constrained and blank-import a toolchain package path."""
    text = (REPO / "tools.go").read_text()
    assert "//go:build" in text or "// +build" in text, (
        "tools.go must be build-constrained; unguarded tools imports fail vendor cells"
    )
    assert "example.org/toolchain/probe" in text
    data = _fresh_report(Path("/tmp/matrix-tools.json"))
    for mode in ("mod", "vendor"):
        assert data["toolchains"]["go1.22"][mode]["status"] == "ok"
        assert data["toolchains"]["go1.23"][mode]["status"] == "ok"


def test_older_profile_clean_with_retained_fork():
    """go1.22 cells stay ok while the retained fork (go 1.23 module) remains in force."""
    data = _fresh_report(Path("/tmp/matrix-lift.json"))
    root = _read_gomod(REPO / "go.mod")
    assert "example.org/httpmux => example.org/httpmux-fork" in root.replace("\n", " ")
    for mode in ("mod", "vendor"):
        cell = data["toolchains"]["go1.22"][mode]
        assert cell["status"] == "ok", cell
        assert cell["selected"]["example.org/httpmux"] == "v0.5.4"
    # The lift is expressed via the root toolchain directive (see matrixci resolve).
    assert re.search(r"(?m)^toolchain\s+go1\.23\s*$", root), (
        "root go.mod must declare toolchain go1.23 so the older profile can keep the fork"
    )


def test_submitted_report_matches_fresh():
    """The agent-submitted report equals what a fresh matrixci invocation produces."""
    submitted = _submitted()
    fresh = _fresh_report(Path("/tmp/matrix-match.json"))
    assert submitted == fresh


def test_proxy_ledger_intact():
    """The module-proxy fixtures match the verifier-side ledger."""
    _assert_ledger(PROXY_LEDGER, PROXY)


def test_policy_ledger_intact():
    """The pin policy document matches the verifier-side ledger."""
    _assert_ledger(POLICY_LEDGER, DOCS)
