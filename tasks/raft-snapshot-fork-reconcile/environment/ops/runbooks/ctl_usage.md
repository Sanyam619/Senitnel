# ctl operator reference

The control binary lives at `/app/bin/ctl`. The Go replay lane lives at `/app/bin/lane`. Operator tables live under `/app/config/l7/` as TOML files; field names are read by the binaries at runtime.

## Operator tables

| Table file | Field | Role |
|------------|-------|------|
| `k9.toml` | `tier_c` | Roll anchor used by the roll phase |
| `m2.toml` | `seq_cutoff` | WAL replay cutoff applied during barrier |
| `p7.toml` | `phases` | Ordered recovery workflow phase list |

Decoy tables (`n3.toml`, `r8.toml`) mirror field names but are not read by `ctl`.

## ctl subcommands

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

Rebuilds the secondary index sidecar for one namespace after barrier application.

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
/app/bin/ctl report --out /output/fork-report.json
```

## lane subcommands

### head

Prints the generation the Go replay lane currently selects for the events namespace.

```
/app/bin/lane head
```

### emit

Writes the lane-side recovery summary JSON using the lane generation picker and on-disk sidecar digests.

```
/app/bin/lane emit --out /output/fork-report.json
```

Rebuild the lane after editing Go sources:

```
cd /app/lane && go build -trimpath -ldflags="-s -w" -o /app/bin/lane ./cmd/lane
```

## Fixture layout

Column stripes live under `/app/data/columns/` (`{namespace}_{stripe}.col` and `{namespace}_merged.col`). Sidecar indexes are `/app/data/sidecars/{namespace}.idx`. Journal chains are under `/app/data/manifests/` (`tier_a.jsonl`, `tier_b.jsonl`, `tier_c.jsonl`). WAL segments are `/app/data/wal/seg_001.bin` and `/app/data/wal/seg_002.bin`. Runtime state is written to `/app/data/state/runtime.json`.

## Notes

- `compact` runs forward compaction against the current head and is unsafe on a partially applied recovery.
- Fast index patch helpers in the store sources do not replace a full rebuild after barrier application.
