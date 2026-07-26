# ctl operator reference

The control binary lives at `/app/bin/ctl`. Basin-window diagnostics live at `/app/bin/window`. Operator tables live under `/app/config/l7/` as TOML files read at runtime. Site trust policy lives under `/app/ops/`. Domain notes for rating-curve and water-balance checks live alongside this runbook.

## Operator tables

TOML files under `/app/config/l7/` hold knobs consulted by `ctl` and `window`. Field names and types are as written in each file. Which knobs a given subcommand reads is determined by binary behavior at runtime.

Relevant tables for the basin-window lane and roll/barrier path:

- `m2.toml` — `scan_tier` names which journal file `/app/bin/window head` scans (`tier_<scan_tier>.jsonl` under `/app/data/manifests/`). `seq_cutoff` feeds `ctl barrier`.
- `k9.toml` — `tier_c` feeds `ctl roll`. `roll_ready` and `journal_pin` also feed `/app/bin/window head` (see Basin-window lane).

## Subcommands

### barrier

```
/app/bin/ctl barrier
```

Applies a WAL sequence cutoff from operator tables, records committed tombstone state into `/app/data/state/runtime.json`, and refreshes the revocation ledger under `/app/data/ledger/`.

### query

```
/app/bin/ctl query point --ks <channel> --key <key> --ts <unix_ms>
/app/bin/ctl query range --ks <channel> --lo <key> --hi <key> --ts <unix_ms>
/app/bin/ctl query aggregate --ks <channel> --ts <unix_ms>
```

Read-only diagnostics: point probe, range scan, and aggregate (count and stage-sum) at a given timestamp.

### rebuild

```
/app/bin/ctl rebuild --ks <channel>
```

Rebuilds the numerical sidecar index for a channel against the current head, applying tombstones present in runtime state. For this incident, rebuild the primary gauge channel (`events`) only. Telemetry (`metrics`) was outside the reload; leave `/app/data/sidecars/metrics.idx` at its pre-reload `bound_gen` and digest.

### report

```
/app/bin/ctl report --out /output/backfill-report.json
```

Emits the basin water-balance summary JSON to the given path. Sidecar digests in the report are taken from the on-disk sidecars produced by rebuild. Refuses to write when lineage, revocation ledger, and sidecar attestation disagree with site trust policy.

### roll

```
/app/bin/ctl roll --ks <channel>
```

Sets the active journal head for a channel using a tier anchor from operator tables. Refuses anchors that violate site trust policy lineage rules.

### status

```
/app/bin/ctl status
```

Read-only runtime snapshot including `active_gen`, `ceiling_gen`, and `wal_seq`.

## Basin-window lane

```
/app/bin/window head
/app/bin/window aggregate --ks <channel> --ts <unix_ms>
```

`window head` opens `/app/data/manifests/tier_<scan_tier>.jsonl` (from `scan_tier` in `m2.toml`) and takes the maximum `gen` in that file. When `roll_ready` in `k9.toml` is false, `journal_pin` in `k9.toml` caps that value whenever the pin is below the scanned maximum. When `roll_ready` is true, the pin is not applied and the scanned-tier maximum stands. After recovery, `window head` equals the restored generation reported by `ctl report`.

`window aggregate` evaluates the merged archive for the requested channel at the given timestamp.

## Fixture layout

Merged gauge archives use the `{channel}_merged.col` filename under `/app/data/columns/`. Sidecar indexes include `/app/data/sidecars/events.idx` and `/app/data/sidecars/metrics.idx`. Journal chains live under `/app/data/manifests/`. WAL segments are under `/app/data/wal/`. Runtime snapshots are written to `/app/data/state/runtime.json`. The revocation ledger lives under `/app/data/ledger/`. Site trust policy lives under `/app/ops/trust_policy.toml`. Rating-window sample keys live under `/app/ops/fixtures/rating_samples.json`.
