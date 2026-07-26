import json
import subprocess
from pathlib import Path

GATECTL = "/app/bin/gatectl"
GRAPH_LAB = "/app/ops/scripts/graph_lab.py"
REPORT_PATH = Path("/output/link-report.json")
DATA = Path("/app/data")
CFG = Path("/app/config/l7")
MODULES = DATA / "modules"
SLOTS_LEDGER = MODULES / "slots.sha256"


def _manifest_head() -> int:
    head = 0
    for path in sorted((DATA / "manifest").glob("tier_*.jsonl")):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            head = max(head, int(rec["epoch"]))
    return head


def _expected(epoch: int) -> dict:
    raw = subprocess.run(
        ["python3", GRAPH_LAB, str(epoch)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return json.loads(raw)


def _config_field(field: str):
    for path in sorted(CFG.glob("*.toml")):
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if not stripped.startswith(f"{field} ="):
                continue
            raw = stripped.split("=", 1)[1].strip()
            if raw.startswith('"'):
                return json.loads(raw)
            return int(raw)
    raise AssertionError(f"missing operator table field {field}")


def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def test_codec_digest_at_head():
    """Codec module digest matches fixture slot at promoted epoch."""
    epoch = _manifest_head()
    expected = _expected(epoch)
    report = json.loads(REPORT_PATH.read_text())
    assert report["modules"]["codec"]["digest"] == expected["modules"]["codec"]["digest"]


def test_host_digest_at_head():
    """Host module digest matches fixture slot at promoted epoch."""
    epoch = _manifest_head()
    expected = _expected(epoch)
    report = json.loads(REPORT_PATH.read_text())
    assert report["modules"]["host"]["digest"] == expected["modules"]["host"]["digest"]


def test_filter_module_present():
    """Filter module appears once manifest epoch reaches three."""
    epoch = _manifest_head()
    expected = _expected(epoch)
    report = json.loads(REPORT_PATH.read_text())
    assert "filter" in report["modules"]
    assert report["modules"]["filter"]["digest"] == expected["modules"]["filter"]["digest"]


def test_visible_module_map_complete():
    """Every fixture-visible module id appears with matching digests."""
    epoch = _manifest_head()
    expected = _expected(epoch)
    report = json.loads(REPORT_PATH.read_text())
    assert set(report["modules"]) == set(expected["modules"])
    for mid, view in expected["modules"].items():
        assert report["modules"][mid]["digest"] == view["digest"]
        assert report["modules"][mid]["version"] == view["version"]


def test_import_table_bindings():
    """Host import table binds dependency slots for the active epoch."""
    epoch = _manifest_head()
    expected = _expected(epoch)
    report = json.loads(REPORT_PATH.read_text())
    assert report["imports"] == expected["imports"]


def test_graph_digest_matches_fixture():
    """Graph digest matches fixture-derived composite at manifest head."""
    epoch = _manifest_head()
    expected = _expected(epoch)
    report = json.loads(REPORT_PATH.read_text())
    assert report["graph_digest"] == expected["graph_digest"]


def test_epoch_matches_manifest_head():
    """Report epoch equals manifest-derived head."""
    head = _manifest_head()
    report = json.loads(REPORT_PATH.read_text())
    assert report["epoch"] == head


def test_gatectl_epoch_alignment():
    """Gate manifest epoch agrees with link report epoch."""
    report = json.loads(REPORT_PATH.read_text())
    gate_epoch = int(_run([GATECTL, "epoch"]))
    assert gate_epoch == report["epoch"]


def test_config_link_epoch_cap_cleared():
    """Operator link epoch ceiling matches promoted manifest head."""
    head = _manifest_head()
    assert _config_field("link_epoch_cap") == head


def test_module_slots_ledger_intact():
    """Module slot fixtures under /app/data/modules/ match slots.sha256."""
    assert SLOTS_LEDGER.is_file(), SLOTS_LEDGER
    for line in SLOTS_LEDGER.read_text().splitlines():
        if not line.strip():
            continue
        want_hash, rel = line.split(None, 1)
        path = MODULES / rel
        assert path.is_file(), rel
        result = subprocess.run(
            ["sha256sum", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.split()[0] == want_hash, rel


def test_output_json_schema_valid():
    """Link report exposes required fields with valid types."""
    assert REPORT_PATH.is_file(), "link report missing"
    payload = json.loads(REPORT_PATH.read_text())
    assert isinstance(payload.get("epoch"), int)
    assert isinstance(payload.get("graph_digest"), str)
    modules = payload.get("modules")
    assert isinstance(modules, dict)
    for view in modules.values():
        assert isinstance(view.get("version"), int)
        assert isinstance(view.get("digest"), str)
        int(view["digest"], 16)
    imports = payload.get("imports")
    assert isinstance(imports, list)
    for row in imports:
        assert isinstance(row.get("import"), str)
        assert isinstance(row.get("slot"), int)
        assert isinstance(row.get("bound"), str)
