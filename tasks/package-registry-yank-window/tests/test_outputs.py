"""Verifier tests for package index yank-window reconciliation."""
import hashlib
import json
import subprocess
from pathlib import Path

ADVSCAN = "/app/bin/advscan"
INDEXCTL = "/app/bin/indexctl"
REPORT_PATH = Path("/output/yank-reconcile.json")
DATA = Path("/app/data")
CFG = Path("/app/config/l7")
CRATES = DATA / "crates"
YANKS = DATA / "yanks"
ADVISORIES = DATA / "advisories"
SNAPSHOTS = DATA / "index" / "snapshots"
# Integrity ledgers live on the verifier side (/tests/ledgers/) so fixture
# rewrites cannot be masked by an agent-side ledger recompute.
LEDGERS = Path("/tests/ledgers")
VERSIONS_LEDGER = LEDGERS / "crates_versions.sha256"
YANKS_LEDGER = LEDGERS / "yanks_inputs.sha256"
ADVISORIES_LEDGER = LEDGERS / "advisories_inputs.sha256"
SNAPSHOTS_LEDGER = LEDGERS / "snapshots.sha256"

SEV_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}
NORMATIVE_CFG = {
    "bound_mode": "half_open",
    "honor_revokes": True,
    "adv_live_only": True,
    "adv_floor": "high",
}


def _load_entries(gen: int) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(CRATES.rglob("*.json")):
        body = json.loads(path.read_text())
        if int(body["gen"]) <= gen:
            rows.append(body)
    rows.sort(key=lambda r: (r["name"], r["vers"]))
    return rows


def _load_revokes() -> dict[tuple[str, str], int]:
    out: dict[tuple[str, str], int] = {}
    revoke_file = Path("/app/data/yanks/revokes.jsonl")
    if not revoke_file.is_file():
        return out
    for line in revoke_file.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        out[(row["crate"], row["vers"])] = int(row["at"])
    return out


def _yank_holds(row: dict, gen: int, half_open: bool, revokes: dict) -> bool:
    if int(row["from"]) > gen:
        return False
    key = (row["crate"], row["vers"])
    if key in revokes and revokes[key] <= gen:
        return False
    until = row.get("until")
    if until is None:
        return True
    if half_open:
        return gen < int(until)
    return gen <= int(until)


def _load_yanked(gen: int, cfg: dict) -> list[dict]:
    half_open = cfg.get("bound_mode") == "half_open"
    honor = bool(cfg.get("honor_revokes", True))
    revokes = _load_revokes() if honor else {}
    out: list[dict] = []
    for line in Path("/app/data/yanks/windows.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if _yank_holds(row, gen, half_open, revokes):
            out.append({"crate": row["crate"], "version": row["vers"]})
    out.sort(key=lambda r: (r["crate"], r["version"]))
    return out


def _is_optional(dep: dict) -> bool:
    return dep.get("kind") == "optional"


def _installable_set(entries: list[dict], yanked: set[tuple[str, str]]) -> list[dict]:
    by_key = {(e["name"], e["vers"]): e for e in entries}
    memo: dict[tuple[str, str], bool] = {}

    def ok(key: tuple[str, str]) -> bool:
        if key in memo:
            return memo[key]
        if key in yanked:
            memo[key] = False
            return False
        body = by_key.get(key)
        if body is None:
            memo[key] = False
            return False
        for dep in body.get("deps", []):
            if _is_optional(dep):
                continue
            dkey = (dep["crate"], dep["version"])
            if not ok(dkey):
                memo[key] = False
                return False
        memo[key] = True
        return True

    out = []
    for body in entries:
        key = (body["name"], body["vers"])
        if ok(key):
            out.append({"crate": body["name"], "version": body["vers"]})
    return out


def _load_advisories(gen: int, yanked: set[tuple[str, str]], cfg: dict) -> list[dict]:
    floor = SEV_RANK.get(str(cfg.get("adv_floor", "high")), 3)
    live_only = bool(cfg.get("adv_live_only", True))
    rows: list[dict] = []
    for line in Path("/app/data/advisories/feed.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if int(row["from"]) > gen:
            continue
        key = (row["crate"], row["vers"])
        if live_only and key not in yanked:
            continue
        if SEV_RANK.get(row.get("severity", "low"), 0) < floor:
            continue
        rows.append(row)
    rows.sort(key=lambda r: (r["crate"], r["vers"]))
    return rows


def _expected(gen: int) -> dict:
    _assert_all_ledgers_intact()
    cfg = dict(NORMATIVE_CFG)
    entries = _load_entries(gen)
    yanked_rows = _load_yanked(gen, cfg)
    yanked_set = {(r["crate"], r["version"]) for r in yanked_rows}
    installable = _installable_set(entries, yanked_set)
    advisories = _load_advisories(gen, yanked_set, cfg)
    canon = {
        "gen": gen,
        "entries": entries,
        "yanked": yanked_rows,
        "advisories": advisories,
    }
    index_digest = hashlib.sha256(
        json.dumps(canon, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    advisory_digest = hashlib.sha256(
        json.dumps({"advisories": advisories}, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    return {
        "snapshot_gen": gen,
        "index_digest": index_digest,
        "installable": installable,
        "yanked": yanked_rows,
        "advisory_digest": advisory_digest,
    }


def _snapshot_head() -> int:
    _assert_ledger(SNAPSHOTS_LEDGER, SNAPSHOTS)
    head = 0
    for path in sorted(SNAPSHOTS.glob("tier_*.jsonl")):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            head = max(head, int(rec["gen"]))
    return head


def _fresh_report(out_path: Path) -> dict:
    subprocess.run(
        [INDEXCTL, "report", "--out", str(out_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(out_path.read_text())


def _config_field(field: str):
    for path in sorted(CFG.glob("*.toml")):
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if not stripped.startswith(f"{field} ="):
                continue
            raw = stripped.split("=", 1)[1].strip()
            if raw.startswith('"'):
                return json.loads(raw)
            if raw in ("true", "false"):
                return raw == "true"
            return int(raw) if raw.isdigit() else raw
    raise AssertionError(f"missing operator table field {field}")


def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _assert_ledger(ledger: Path, root: Path) -> None:
    assert ledger.is_file(), ledger
    for line in ledger.read_text().splitlines():
        if not line.strip():
            continue
        want_hash, rel = line.split(None, 1)
        target = root.joinpath(rel)
        assert target.is_file(), rel
        got = hashlib.sha256(target.read_bytes()).hexdigest()
        assert got == want_hash, rel


def _assert_all_ledgers_intact() -> None:
    """Fail early if any fixture bytes drift from the verifier ledger.

    This is called from `_expected()` and `_snapshot_head()` so that every
    downstream comparison uses pinned inputs; any tamper of fixtures shows up
    as an assertion failure at the first test that touches them, regardless
    of test ordering.
    """
    _assert_ledger(VERSIONS_LEDGER, CRATES)
    _assert_ledger(YANKS_LEDGER, YANKS)
    _assert_ledger(ADVISORIES_LEDGER, ADVISORIES)
    _assert_ledger(SNAPSHOTS_LEDGER, SNAPSHOTS)


def test_indexctl_report_rerun_matches_output_and_policy():
    """Fresh indexctl report must match /output and the normative policy."""
    gen = _snapshot_head()
    expected = _expected(gen)
    submitted = json.loads(REPORT_PATH.read_text())
    fresh = _fresh_report(Path("/tmp/yank-reconcile-fresh.json"))
    assert fresh == submitted
    assert fresh["snapshot_gen"] == expected["snapshot_gen"]
    assert fresh["index_digest"] == expected["index_digest"]
    assert fresh["advisory_digest"] == expected["advisory_digest"]
    assert sorted(fresh["installable"], key=lambda r: (r["crate"], r["version"])) == sorted(
        expected["installable"], key=lambda r: (r["crate"], r["version"])
    )
    assert sorted(fresh["yanked"], key=lambda r: (r["crate"], r["version"])) == sorted(
        expected["yanked"], key=lambda r: (r["crate"], r["version"])
    )


def test_exclusive_upper_bound_clears_yank():
    """A yank window that ends at the head generation is not active at the head."""
    gen = _snapshot_head()
    expected = _expected(gen)
    report = _fresh_report(Path("/tmp/yank-reconcile-bound.json"))
    yanked = {(r["crate"], r["version"]) for r in report["yanked"]}
    assert ("gamma-api", "0.9.1") not in yanked
    assert ("beta-util", "1.3.0") not in yanked
    assert yanked == {(r["crate"], r["version"]) for r in expected["yanked"]}


def test_open_ended_yank_remains_active():
    """Open-ended yank windows without a revoke remain active at the head."""
    report = _fresh_report(Path("/tmp/yank-reconcile-open.json"))
    yanked = {(r["crate"], r["version"]) for r in report["yanked"]}
    assert ("beta-util", "1.2.0") in yanked
    assert ("sigma-kit", "0.1.0") in yanked


def test_revoke_clears_open_ended_yank():
    """A revoke at or before the head clears an otherwise open-ended yank."""
    report = _fresh_report(Path("/tmp/yank-reconcile-revoke.json"))
    yanked = {(r["crate"], r["version"]) for r in report["yanked"]}
    installable = {(r["crate"], r["version"]) for r in report["installable"]}
    assert ("theta-lib", "0.2.0") not in yanked
    assert ("theta-lib", "0.2.0") in installable


def test_direct_yanked_dep_blocks_consumer():
    """A required pin onto an actively yanked version is not installable."""
    report = _fresh_report(Path("/tmp/yank-reconcile-direct.json"))
    installable = {(r["crate"], r["version"]) for r in report["installable"]}
    assert ("alpha-core", "1.1.0") not in installable
    assert ("delta-cli", "2.1.0") not in installable


def test_transitive_yank_blocks_indirect_consumer():
    """A package whose required chain reaches an active yank is not installable."""
    report = _fresh_report(Path("/tmp/yank-reconcile-transitive.json"))
    installable = {(r["crate"], r["version"]) for r in report["installable"]}
    assert ("epsilon-net", "1.0.0") not in installable


def test_optional_yanked_dep_does_not_block():
    """Optional dependency edges onto yanked versions do not block installability."""
    report = _fresh_report(Path("/tmp/yank-reconcile-optional.json"))
    installable = {(r["crate"], r["version"]) for r in report["installable"]}
    assert ("omega-lib", "1.0.0") in installable


def test_restored_chain_allows_nested_consumer():
    """Consumers remain installable when an intermediate yank window has ended."""
    report = _fresh_report(Path("/tmp/yank-reconcile-restored.json"))
    installable = {(r["crate"], r["version"]) for r in report["installable"]}
    assert ("delta-cli", "2.0.0") in installable
    assert ("zeta-tool", "1.0.0") in installable
    assert ("gamma-api", "0.9.1") in installable


def test_installable_map_complete():
    """Full installable and yanked sets match the fixture-derived reference."""
    gen = _snapshot_head()
    expected = _expected(gen)
    report = _fresh_report(Path("/tmp/yank-reconcile-map.json"))
    got_i = sorted(report["installable"], key=lambda r: (r["crate"], r["version"]))
    exp_i = sorted(expected["installable"], key=lambda r: (r["crate"], r["version"]))
    assert got_i == exp_i
    got_y = sorted(report["yanked"], key=lambda r: (r["crate"], r["version"]))
    exp_y = sorted(expected["yanked"], key=lambda r: (r["crate"], r["version"]))
    assert got_y == exp_y


def test_index_digest_matches_fixture():
    """Index digest matches fixture-derived composite at snapshot head."""
    gen = _snapshot_head()
    expected = _expected(gen)
    report = _fresh_report(Path("/tmp/yank-reconcile-index.json"))
    assert report["index_digest"] == expected["index_digest"]


def test_advisory_excludes_expired_and_revoked():
    """Advisory digest excludes ended windows, revoked yanks, and sub-floor rows."""
    gen = _snapshot_head()
    expected = _expected(gen)
    report = _fresh_report(Path("/tmp/yank-reconcile-adv.json"))
    assert report["advisory_digest"] == expected["advisory_digest"]
    yanked = {(r["crate"], r["version"]) for r in report["yanked"]}
    assert ("gamma-api", "0.9.1") not in yanked
    assert ("theta-lib", "0.2.0") not in yanked


def test_advisory_severity_floor_drops_live_low():
    """A live yank with below-floor severity does not change the advisory digest alone."""
    gen = _snapshot_head()
    expected = _expected(gen)
    report = _fresh_report(Path("/tmp/yank-reconcile-floor.json"))
    yanked = {(r["crate"], r["version"]) for r in report["yanked"]}
    assert ("sigma-kit", "0.1.0") in yanked
    assert report["advisory_digest"] == expected["advisory_digest"]


def test_advscan_digest_alignment():
    """Advisory scanner digest agrees with a fresh reconcile report advisory_digest."""
    report = _fresh_report(Path("/tmp/yank-reconcile-scan.json"))
    scan_digest = _run([ADVSCAN, "digest"])
    assert scan_digest == report["advisory_digest"]


def test_snapshot_gen_matches_head():
    """Report snapshot generation equals snapshot-derived head."""
    head = _snapshot_head()
    report = _fresh_report(Path("/tmp/yank-reconcile-gen.json"))
    assert report["snapshot_gen"] == head


def test_advscan_window_alignment():
    """Advisory scanner window agrees with reconcile report generation."""
    report = _fresh_report(Path("/tmp/yank-reconcile-window.json"))
    scan_gen = int(_run([ADVSCAN, "window"]))
    assert scan_gen == report["snapshot_gen"]


def test_operator_policies_armed():
    """Operator tables enable half-open bounds, revokes, live advisories, and high floor."""
    assert _config_field("bound_mode") == "half_open"
    assert _config_field("honor_revokes") is True
    assert _config_field("adv_live_only") is True
    assert _config_field("adv_floor") == "high"


def test_crate_versions_ledger_intact():
    """Crate version fixtures match the verifier-side ledger under /tests/ledgers/."""
    _assert_ledger(VERSIONS_LEDGER, CRATES)


def test_yank_inputs_ledger_intact():
    """Yank window and revoke fixtures match the verifier-side ledger under /tests/ledgers/."""
    _assert_ledger(YANKS_LEDGER, YANKS)


def test_advisory_inputs_ledger_intact():
    """Advisory feed fixtures match the verifier-side ledger under /tests/ledgers/."""
    _assert_ledger(ADVISORIES_LEDGER, ADVISORIES)


def test_index_snapshots_ledger_intact():
    """Promoted snapshot fixtures match the verifier-side ledger under /tests/ledgers/."""
    _assert_ledger(SNAPSHOTS_LEDGER, SNAPSHOTS)


def test_output_json_schema_valid():
    """Reconcile report exposes required fields with valid types."""
    assert REPORT_PATH.is_file(), "yank reconcile report missing"
    payload = json.loads(REPORT_PATH.read_text())
    assert isinstance(payload.get("snapshot_gen"), int)
    assert isinstance(payload.get("index_digest"), str)
    int(payload["index_digest"], 16)
    for row in payload.get("installable", []):
        assert isinstance(row.get("crate"), str)
        assert isinstance(row.get("version"), str)
    for row in payload.get("yanked", []):
        assert isinstance(row.get("crate"), str)
        assert isinstance(row.get("version"), str)
    assert isinstance(payload.get("advisory_digest"), str)
    int(payload["advisory_digest"], 16)
