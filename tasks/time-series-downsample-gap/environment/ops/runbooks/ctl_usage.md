# ctl operator reference

The control binary lives at `/app/bin/ctl`. Operator tables live under `/app/config/l7/` as TOML files read at runtime.

## Operator tables

| Table file | Field | Role |
|------------|-------|------|
| `k9.toml` | `tier_c` | Roll anchor used by the roll phase |
| `m2.toml` | `seq_cutoff` | WAL replay cutoff applied during barrier |
| `p7.toml` | `phases` | Ordered recovery workflow phase list |

Decoy tables (`n3.toml`, `r8.toml`) mirror field names but are not read by `ctl`.

## Subcommands

### roll

Rolls the active journal head for one namespace using the tier anchor from operator tables.

```
/app/bin/ctl roll --ks <namespace>
```

### barrier

Applies the WAL replay cutoff from operator tables and records tombstone keys into `/app/data/state/runtime.json`.

```
/app/bin/ctl barrier
```

### rebuild

Rebuilds the rollup sidecar index for one namespace after barrier application.

```
/app/bin/ctl rebuild --ks <namespace>
```

### status

Read-only runtime snapshot (`active_gen`, `ceiling_gen`, `wal_seq`).

```
/app/bin/ctl status
```

### query

Read-only diagnostics. Supports point, range, and aggregate modes.

```
/app/bin/ctl query point --ks <namespace> --key <key> --ts <unix_ms>
/app/bin/ctl query range --ks <namespace> --lo <key> --hi <key> --ts <unix_ms>
/app/bin/ctl query aggregate --ks <namespace> --ts <unix_ms>
```

### report

Emits the recovery summary JSON.

```
/app/bin/ctl report --out /output/rewind-report.json
```

## Fixture layout

Merged namespace stripes use the `{namespace}_merged.col` filename under `/app/data/columns/`. Sidecar indexes are `/app/data/sidecars/{namespace}.idx`. Journal chains live under `/app/data/manifests/`. WAL segments are under `/app/data/wal/`. Runtime snapshots are written to `/app/data/state/runtime.json`.

## Notes

- `compact` runs forward downsample compaction against the current head and is unsafe on a partially applied recovery.
- Fast index patch helpers exist in the codebase but do not replace a full rebuild after barrier application.
