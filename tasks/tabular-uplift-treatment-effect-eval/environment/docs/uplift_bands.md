# Uplift treatment-effect evaluation bands

`schema_tag` must be `uplift-eval-v1`.

## Tip resolution

Every slice row must carry the selected durable assignment tip drawn from
materials under `/app/data/feature_registry/`. Sheets kept under
`/app/data/ledger/` are operator mirrors and are not the selection authority.
Retired tip ids are not selected. Live observational tips are not selected.

`treatment_tip` is a number: the epoch of the selected tip, not its string id.

## Propensity

`propensity` must be the durable estimator bound from that tip
(`ipw`, `dr`, or `tmle`). Surface decoy labels are not accepted.

## Scored columns

Each sheet under `/app/data/outcomes/` publishes more than one scored AUUC
and Qini column plus an observational column. The estimator roster under
`/app/data/estimators/` records which scored column belongs to each
estimator; a published `auuc` and `qini` pair must be the column that roster
assigns to the bound estimator. The roster copy kept beside the operator
sheets in `/app/data/ledger/` is a stale generation and is not the roster
authority; reading it lands metrics outside the bands below.

## Tip bind receipt

Evaluation only leaves trial mode when `/app/calib/tip_bind.accept` exists
and agrees with the registry-resolved durable tip. The receipt is a plain
`key = value` sheet, one pair per line, naming the resolved `tip`, its
`epoch`, and its `propensity`.

## Slices

Each entry in `slices[]` has `id`, `auuc`, `qini`, `treatment_tip`, and
`propensity`.

- `treatment_tip` and `propensity` are identical across every slice row.
- Outcomes under `/app/data/outcomes/`, treatments under `/app/data/treat/`,
  and features under `/app/data/feat/` participate in scoring.

### AUUC bands

| slice id  | min   | max   |
| --------- | ----- | ----- |
| s_alpha   | 0.406 | 0.418 |
| s_beta    | 0.432 | 0.444 |
| s_gamma   | 0.459 | 0.471 |
| s_delta   | 0.385 | 0.397 |
| s_epsilon | 0.418 | 0.430 |

### Qini bands

| slice id  | min   | max   |
| --------- | ----- | ----- |
| s_alpha   | 0.262 | 0.274 |
| s_beta    | 0.285 | 0.297 |
| s_gamma   | 0.309 | 0.321 |
| s_delta   | 0.242 | 0.254 |
| s_epsilon | 0.273 | 0.285 |

## eval_ok

`eval_ok` is true only when every slice lands inside its band and the run's
internal invariants hold. A shallow print from `/app/tools/upliftprobe` is
not sufficient evidence of a healthy run.

## Idempotence

Two consecutive runs of the eval driver must write byte-identical
`/output/uplift-eval.json`.
