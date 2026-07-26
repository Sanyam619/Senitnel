"""Verifier for packlab bundle reconciliation outcomes."""

import json
import subprocess

import pytest
from pathlib import Path

REPORT = Path("/output/reconcile-report.json")
ANCHOR = Path("/data/images")
ROWS_DIR = Path("/tests/rows")
PACKCTL = Path("/opt/packlab/bin/packctl")
BUNDLE_IDS = ["bundle-x7", "bundle-m4", "bundle-k9", "bundle-r2", "bundle-n5"]


def _expected_bundle(bundle_id: str) -> dict:
    return json.loads((ROWS_DIR / f"{bundle_id}.json").read_text(encoding="utf-8"))


def _load_report() -> dict:
    assert REPORT.is_file(), f"missing {REPORT}"
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _by_id(payload: dict) -> dict[str, dict]:
    bundles = payload.get("bundles")
    assert isinstance(bundles, list), payload
    return {row["id"]: row for row in bundles if isinstance(row, dict) and "id" in row}


def test_v8_schema_bundle():
    """Report version, bundle ids, and digest prefixes match the lab contract."""
    payload = _load_report()
    assert payload.get("version") == 1
    rows = _by_id(payload)
    for bid in BUNDLE_IDS:
        assert bid in rows, sorted(rows)
        row = rows[bid]
        assert isinstance(row.get("stacks"), list) and row["stacks"]
        assert all(isinstance(d, str) and d.startswith("sha256:") for d in row["stacks"])
        paths = row.get("paths")
        assert isinstance(paths, dict)
        for path, digest in paths.items():
            assert isinstance(path, str) and path
            assert isinstance(digest, str) and digest.startswith("sha256:")


def test_c1_packctl_regenerates_report():
    """The installed packctl CLI reproduces the on-disk reconcile report."""
    tmp = Path("/tmp/packctl-verify-report.json")
    tmp.unlink(missing_ok=True)
    subprocess.run(
        [str(PACKCTL), "--root", str(ANCHOR), "--out", str(tmp)],
        check=True,
        capture_output=True,
        text=True,
    )
    regen = json.loads(tmp.read_text(encoding="utf-8"))
    assert regen == _load_report()


@pytest.mark.parametrize("bundle_id", BUNDLE_IDS)
def test_stacks_match(bundle_id: str):
    """Each bundle stack list matches the expected canonical order."""
    row = _by_id(_load_report())[bundle_id]
    assert row["stacks"] == _expected_bundle(bundle_id)["stacks"]


@pytest.mark.parametrize("bundle_id", BUNDLE_IDS)
def test_paths_match(bundle_id: str):
    """Each bundle path map matches the expected merged view."""
    row = _by_id(_load_report())[bundle_id]
    assert row["paths"] == _expected_bundle(bundle_id)["paths"]


def test_r6_anchor_intact():
    """Bundle blobs under the data root were not rewritten."""
    manifest = ANCHOR / "anchor.sha256"
    assert manifest.is_file(), manifest
    for line in manifest.read_text(encoding="utf-8").splitlines():
        want_hash, rel = line.split(None, 1)
        path = ANCHOR / rel
        assert path.is_file(), rel
        result = subprocess.run(
            ["sha256sum", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.split()[0] == want_hash, rel
