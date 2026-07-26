# Diarization evaluation bands

`schema_tag` must be `diar-eval-v1`.

## Tip resolution

Every slice row must carry the selected sealed embedding-bank tip drawn from
materials under `/app/data/embed_registry/`. Retired tip ids are not
selected. Live observational tips are not selected.

`tip_epoch` is a number: the epoch of the selected embedding tip, not its
string id.

## Clustering method

`clustering` must be the durable method tip drawn from materials under
`/app/data/cluster_registry/` and must be one of `ahc`, `spectral`, or
`nme`. Live decoy methods are not accepted. Sheets under
`/app/data/ledger/` are operator mirrors and are not the method authority.

## Scored columns

Each audio sheet under `/app/data/audio/` publishes DER and JER columns for
several method×epoch combinations plus an observational column and an
oracle-count column. A published `der` and `jer` pair must be the column
keyed by the bound durable method and the bound embedding tip epoch.
Oracle speaker-count columns are not the unsupervised evaluation path.

## Tip bind receipt

Evaluation only leaves trial mode when `/app/calib/tip_bind.accept` exists
and agrees with the registry-resolved durable tips. The receipt is a plain
`key = value` sheet, one pair per line, naming the resolved embedding `tip`,
its `epoch`, the durable `clustering` label, and the cluster `method` tip
id.

## Slices

Each entry in `slices[]` has `id`, `der`, `jer`, `clustering`, and
`tip_epoch`.

- `clustering` and `tip_epoch` are identical across every slice row.
- Audio under `/app/data/audio/` and RTTM under `/app/data/rttm/` participate
  in scoring.

### DER bands

| slice id  | min   | max   |
| --------- | ----- | ----- |
| s_meet_a  | 0.092 | 0.104 |
| s_meet_b  | 0.106 | 0.118 |
| s_call_c  | 0.081 | 0.093 |
| s_call_d  | 0.119 | 0.131 |
| s_far_e   | 0.135 | 0.147 |

### JER bands

| slice id  | min   | max   |
| --------- | ----- | ----- |
| s_meet_a  | 0.126 | 0.138 |
| s_meet_b  | 0.142 | 0.154 |
| s_call_c  | 0.115 | 0.127 |
| s_call_d  | 0.155 | 0.167 |
| s_far_e   | 0.172 | 0.184 |

## eval_ok

`eval_ok` is true only when every slice lands inside its band and the run's
internal unsupervised invariants hold. A shallow print from
`/app/tools/diarprobe` that relies on oracle speaker counts is not
sufficient evidence of a healthy run.

## Idempotence

Two consecutive runs of the eval driver must write byte-identical
`/output/diar-eval.json`.
