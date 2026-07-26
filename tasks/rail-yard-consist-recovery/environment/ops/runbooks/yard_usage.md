# yard consist export contract

## Promoted movement head

Compute the promoted head as the maximum `seq` across every `/app/data/movements/tier_*.jsonl` record. A live `lane probe` value, a single-tier head, or a pin cleared to `0` is not the promoted head unless it equals that maximum.

## Operator tables (`/app/config/l7/*.toml`)

| Field | Required end state |
|-------|--------------------|
| `journal_pin` | equal to the promoted movement head (pin to that head; do not clear to `0`) |
| `seq_floor` | equal to the promoted movement head |
| `replay_gate` | `0` so pull operations apply during reconstruction |
| `tier_reducer` | `"max"` so the movement audit selects the promoted head across tiers |

## Runtime and inputs

- `/app/data/state/runtime.json` → `active_seq` must equal the promoted movement head.
- Do not hand-edit car registry fixtures under `/app/data/cars/`.
- Do not modify the shipped reporting tools under `/app/bin/`.

## Report and probes

- `/app/bin/yardctl report --out PATH` emits JSON with `replay_seq`, `tracks`, and `audit_digest`.
- `/app/bin/lane probe` prints the replay sequence selected by the movement audit lane.
- `/app/ops/scripts/consist_lab.py SEQ` prints the fixture-derived track map and audit digest for a replay sequence; the delivered report must match that probe at the promoted head.
