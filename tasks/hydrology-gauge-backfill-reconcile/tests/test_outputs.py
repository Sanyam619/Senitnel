import json
import subprocess
from pathlib import Path

CTL = "/app/bin/ctl"
WINDOW = "/app/bin/window"
REPORT_PATH = Path("/output/backfill-report.json")
RUNTIME_PATH = Path("/app/data/state/runtime.json")
CFG = Path("/app/config/l7")
QUERY_TS = 550
TELEMETRY_TS = 100
PRIMARY = "events"
SECONDARY = "metrics"

# Frozen verifier baselines (not recomputed from agent-writable answers alone).
# Domain sample tokens also appear under /app/ops/fixtures/rating_samples.json.
_ANCHOR = 17
_STATIONS_SEGMENTS = 2
_TELEMETRY_SEGMENTS = 2


def _ctl_json(args: list[str]) -> dict:
    result = subprocess.run(
        [CTL, *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout.strip())


def _window_json(args: list[str]) -> dict:
    result = subprocess.run(
        [WINDOW, *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout.strip())


def _window_head() -> int:
    return int(
        subprocess.run([WINDOW, "head"], check=True, capture_output=True, text=True).stdout.strip()
    )


def _load_report() -> dict:
    assert REPORT_PATH.is_file(), "backfill report missing"
    return json.loads(REPORT_PATH.read_text())


def _load_runtime() -> dict:
    return json.loads(RUNTIME_PATH.read_text())


def _config_field(field: str):
    """Read a single field from whichever operator table defines it."""
    for path in sorted(CFG.glob("*.toml")):
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if not stripped.startswith(f"{field} ="):
                continue
            raw = stripped.split("=", 1)[1].strip()
            if raw.startswith("["):
                return json.loads(raw)
            if raw.startswith('"'):
                return json.loads(raw)
            if raw in ("true", "false"):
                return raw == "true"
            return int(raw)
    raise AssertionError(f"missing operator table field {field}")


def _discover_roll_anchor() -> int:
    """Last events generation in tier_b before the tainted stripe-99 cutover."""
    anchor = None
    for line in Path("/app/data/manifests/tier_b.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("ns") != "events":
            continue
        if 99 in rec.get("stripes", []):
            break
        anchor = int(rec["gen"])
    if anchor is None:
        raise AssertionError("could not derive roll anchor from tier_b journal")
    return anchor


def _manifest_stripes_at(ns: str, gen: int) -> list[int]:
    """Stripe list for a namespace at a journal generation."""
    entries: list[dict] = []
    for name in ("tier_a.jsonl", "tier_b.jsonl", "tier_c.jsonl"):
        path = Path(f"/app/data/manifests/{name}")
        if not path.is_file():
            continue
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            entries.append(json.loads(line))
    matching = [entry for entry in entries if entry.get("ns") == ns and int(entry["gen"]) <= gen]
    if not matching:
        raise AssertionError(f"no journal entry for {ns} gen {gen}")
    latest = max(matching, key=lambda entry: int(entry["gen"]))
    return [int(stripe) for stripe in latest["stripes"]]


def _stripe_col_path(ns: str, stripe_id: int) -> Path:
    if stripe_id == 99:
        return Path(f"/app/data/columns/{ns}_merged.col")
    return Path(f"/app/data/columns/{ns}_{stripe_id:03}.col")


def _sha256_stripe_bytes(paths: list[Path]) -> str:
    """SHA256 hex over concatenated raw stripe file bytes in manifest order."""
    blob = b"".join(path.read_bytes() for path in paths)
    result = subprocess.run(
        ["openssl", "dgst", "-sha256"],
        input=blob,
        check=True,
        capture_output=True,
    )
    return result.stdout.decode().strip().split("= ", 1)[1].replace(":", "").strip()


def _expected_sidecar_digest(ns: str, anchor: int) -> str:
    stripes = _manifest_stripes_at(ns, anchor)
    paths = [_stripe_col_path(ns, stripe_id) for stripe_id in stripes]
    return _sha256_stripe_bytes(paths)


def _expected_sidecar_map(ns: str, anchor: int, tombstone_keys: set[str]) -> dict[str, int]:
    """Key-to-stripe map after rebuild, excluding applied tombstones."""
    runtime = _load_runtime()
    wal_seq = int(runtime.get("wal_seq", 0))
    tombstone_seq = int(runtime.get("tombstone_seq", 0))
    mapping: dict[str, int] = {}
    for stripe_id in _manifest_stripes_at(ns, anchor):
        stripe = json.loads(_stripe_col_path(ns, stripe_id).read_text())
        stripe_num = int(stripe["id"])
        for row in stripe["records"]:
            key = row["k"]
            if key in tombstone_keys and wal_seq >= tombstone_seq and tombstone_seq > 0:
                continue
            mapping[key] = stripe_num
    return mapping


def _discover_barrier_cutoff() -> tuple[int, str]:
    """WAL sequence and tombstoned key at the barrier cutoff fixture."""
    tombstone_seq = None
    tombstone_key = None
    for name in ("seg_001.bin", "seg_002.bin"):
        blob = (Path("/app/data/wal") / name).read_bytes()
        if blob[:4] != b"WLOG":
            raise AssertionError(f"bad wal magic in {name}")
        off = 4
        while off + 11 <= len(blob):
            seq = int.from_bytes(blob[off : off + 8], "little")
            off += 8
            op = blob[off]
            off += 1
            key_len = int.from_bytes(blob[off : off + 2], "little")
            off += 2
            key = blob[off : off + key_len].decode()
            off += key_len
            off += 8
            if op == 1:
                tombstone_seq = seq
                tombstone_key = key
    if tombstone_seq is None or tombstone_key is None:
        raise AssertionError("could not locate tombstone cutoff in wal segments")
    return tombstone_seq, tombstone_key


def test_fixture_vector_alpha():
    """Primary gauge keys resolve to expected payloads at the query timestamp."""
    got_alpha = _ctl_json(["query", "point", "--ks", PRIMARY, "--key", "alpha", "--ts", str(QUERY_TS)])
    got_beta = _ctl_json(["query", "point", "--ks", PRIMARY, "--key", "beta", "--ts", str(QUERY_TS)])
    got_gamma = _ctl_json(["query", "point", "--ks", PRIMARY, "--key", "gamma", "--ts", str(QUERY_TS)])

    assert got_alpha["found"] is True
    assert got_alpha["value"] == "payload_a"
    assert got_alpha["ts"] == 100

    assert got_beta["found"] is True
    assert got_beta["value"] == "payload_b"

    assert got_gamma["found"] is True
    assert got_gamma["value"] == "payload_c"


def test_fixture_vector_beta():
    """Range scan returns keys in sorted order with stable payload values."""
    payload = _ctl_json(
        [
            "query",
            "range",
            "--ks",
            PRIMARY,
            "--lo",
            "alpha",
            "--hi",
            "gamma",
            "--ts",
            str(QUERY_TS),
        ]
    )
    keys = [hit["key"] for hit in payload["hits"]]
    assert keys == ["alpha", "beta", "gamma"]
    values = [hit["value"] for hit in payload["hits"]]
    assert values == ["payload_a", "payload_b", "payload_c"]


def test_absent_marker_at_window():
    """Tombstoned gauge marker stays absent for the queried time window."""
    wal_cutoff, tombstone_key = _discover_barrier_cutoff()
    config_cutoff = _config_field("seq_cutoff")
    payload = _ctl_json(
        ["query", "point", "--ks", PRIMARY, "--key", tombstone_key, "--ts", str(QUERY_TS)]
    )
    assert payload["found"] is False
    runtime = _load_runtime()
    assert config_cutoff >= wal_cutoff
    assert runtime["tombstone_seq"] == config_cutoff


def test_aggregate_totals_stable():
    """Channel aggregate totals match the frozen stage-sum baseline at the query window."""
    payload = _ctl_json(["query", "aggregate", "--ks", PRIMARY, "--ts", str(QUERY_TS)])
    assert payload["count"] == 3
    assert payload["sum_ts"] == 600


def test_basin_window_aggregate_alignment():
    """Basin-window lane totals agree with numerical rollup probes at the query epoch."""
    ctl = _ctl_json(["query", "aggregate", "--ks", PRIMARY, "--ts", str(QUERY_TS)])
    basin = _window_json(["aggregate", "--ks", PRIMARY, "--ts", str(QUERY_TS)])
    assert basin["count"] == 3
    assert basin["sum_ts"] == 600
    assert ctl["count"] == basin["count"]
    assert ctl["sum_ts"] == basin["sum_ts"]


def test_basin_window_head_alignment():
    """Basin-window head matches the restored generation reported by ctl."""
    head = _window_head()
    report = _load_report()
    assert head == report["restored_generation"]
    assert head == _ANCHOR
    assert head == _discover_roll_anchor()


def test_output_json_schema_valid():
    """Backfill report JSON exposes required fields with valid types and values."""
    payload = _load_report()

    assert isinstance(payload.get("restored_generation"), int)
    for ns in ("stations", "telemetry"):
        block = payload.get(ns)
        assert isinstance(block, dict)
        assert isinstance(block.get("visible_segments"), int)
        digest = block.get("sidecar_digest")
        assert isinstance(digest, str)
        assert len(digest) >= 16
        int(digest, 16)

    status = _ctl_json(["status"])
    assert 0 < payload["restored_generation"] <= status["ceiling_gen"]
    assert payload["restored_generation"] == _ANCHOR


def test_report_visible_segments_match_journal():
    """Report visible_segments match the frozen stripe counts at the restored generation."""
    payload = _load_report()
    assert payload["restored_generation"] == _ANCHOR
    assert payload["stations"]["visible_segments"] == _STATIONS_SEGMENTS
    assert payload["telemetry"]["visible_segments"] == _TELEMETRY_SEGMENTS
    assert payload["stations"]["visible_segments"] == len(
        _manifest_stripes_at(PRIMARY, _discover_roll_anchor())
    )


def test_chain_order_invariant():
    """Restored report generation stays at or below the ctl status ceiling."""
    status = _ctl_json(["status"])
    runtime = _load_runtime()
    payload = _load_report()
    restored = payload["restored_generation"]
    anchor = _discover_roll_anchor()

    assert 0 < restored <= status["ceiling_gen"]
    assert restored == _ANCHOR
    assert restored == runtime["active_gen"]
    assert runtime["active_gen"] == anchor
    assert payload["stations"]["visible_segments"] == _STATIONS_SEGMENTS
    assert payload["telemetry"]["visible_segments"] == _TELEMETRY_SEGMENTS


def test_barrier_tombstone_runtime_state():
    """Barrier replay committed tombstone state tied to the WAL cutoff fixture."""
    runtime = _load_runtime()
    wal_cutoff, tombstone_key = _discover_barrier_cutoff()
    config_cutoff = _config_field("seq_cutoff")

    assert config_cutoff >= wal_cutoff
    assert runtime["tombstone_seq"] == config_cutoff
    assert runtime["wal_seq"] >= wal_cutoff
    assert tombstone_key in runtime["tombstone_keys"]

    ledger_path = Path("/app/data/ledger/revocations.jsonl")
    assert ledger_path.is_file()
    ledger_keys = set()
    for line in ledger_path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("key") == "stale_placeholder":
            continue
        ledger_keys.add(rec["key"])
    assert tombstone_key in ledger_keys

    point = _ctl_json(
        ["query", "point", "--ks", PRIMARY, "--key", tombstone_key, "--ts", str(QUERY_TS)]
    )
    assert point["found"] is False

    scanned = _ctl_json(
        [
            "query",
            "range",
            "--ks",
            PRIMARY,
            "--lo",
            tombstone_key,
            "--hi",
            tombstone_key,
            "--ts",
            str(QUERY_TS),
        ]
    )
    keys = [hit["key"] for hit in scanned["hits"]]
    assert tombstone_key not in keys

    aggregate = _ctl_json(["query", "aggregate", "--ks", PRIMARY, "--ts", str(QUERY_TS)])
    assert aggregate["count"] == 3


def test_lineage_rejects_merged_contamination():
    """Restored generation's journal stripe set excludes merged contamination stripes."""
    report = _load_report()
    restored = report["restored_generation"]
    stripes = _manifest_stripes_at(PRIMARY, restored)
    # Contaminated cutover uses stripe id 99 in later journal rows.
    assert 99 not in stripes
    assert restored == _discover_roll_anchor()


def test_recovery_config_anchors():
    """Recovered generation anchors agree across report, window head, runtime, and status."""
    status = _ctl_json(["status"])
    report = _load_report()
    head = _window_head()
    runtime = _load_runtime()
    anchor = _discover_roll_anchor()

    assert report["restored_generation"] == _ANCHOR
    assert head == _ANCHOR
    assert runtime["active_gen"] == anchor
    assert _config_field("tier_c") == anchor
    assert 0 < report["restored_generation"] <= status["ceiling_gen"]


def test_rebuild_generation_alignment():
    """Rebuilt events sidecar is bound to the rolled generation with a full key map."""
    runtime = _load_runtime()
    anchor = _discover_roll_anchor()
    _cutoff, tombstone_key = _discover_barrier_cutoff()
    sidecar = json.loads(Path("/app/data/sidecars/events.idx").read_text())
    expected_map = _expected_sidecar_map(PRIMARY, anchor, {tombstone_key})
    report = _load_report()

    assert report["restored_generation"] == _ANCHOR
    assert runtime["active_gen"] == anchor
    assert sidecar["bound_gen"] == anchor
    assert runtime["sidecar_gen"]["events"] == anchor
    assert sidecar["map"] == expected_map
    assert tombstone_key not in sidecar["map"]


def test_digest_checksum_match():
    """Events sidecar digest matches stripe SHA256 and the report stations entry."""
    anchor = _discover_roll_anchor()
    runtime = _load_runtime()
    assert runtime["active_gen"] == anchor
    payload = _load_report()
    sidecar = json.loads(Path("/app/data/sidecars/events.idx").read_text())
    expected = _expected_sidecar_digest(PRIMARY, anchor)

    assert sidecar["bound_gen"] == anchor
    assert sidecar["digest"] == expected
    assert payload["stations"]["sidecar_digest"] == expected
    assert payload["stations"]["sidecar_digest"] == sidecar["digest"]


def test_secondary_namespace_stable():
    """Unaffected telemetry channel probes remain at baseline; report digest matches sidecar."""
    point = _ctl_json(["query", "point", "--ks", SECONDARY, "--key", "m1", "--ts", str(TELEMETRY_TS)])
    agg = _ctl_json(["query", "aggregate", "--ks", SECONDARY, "--ts", str(TELEMETRY_TS)])

    assert point["found"] is True
    assert point["key"] == "m1"
    assert point["value"] == "metric_one"
    assert point["ts"] == 50

    assert agg["count"] == 3
    assert agg["sum_ts"] == 215

    report = _load_report()
    metrics_sidecar = json.loads(Path("/app/data/sidecars/metrics.idx").read_text())
    assert metrics_sidecar["bound_gen"] < _ANCHOR
    assert report["telemetry"]["visible_segments"] == _TELEMETRY_SEGMENTS
    assert report["telemetry"]["sidecar_digest"] == metrics_sidecar["digest"]


def test_prebuilt_runtime_binaries():
    """Recovery relies on prebuilt ctl and window binaries without rebuilding /app/store or /app/lane."""
    for path in ("/app/bin/ctl", "/app/bin/window"):
        payload = Path(path).read_bytes()
        assert payload[:4] == b"\x7fELF", f"{path} must remain a shipped binary"
    assert Path("/app/store/Cargo.toml").is_file()
    assert Path("/app/lane/go.mod").is_file()
