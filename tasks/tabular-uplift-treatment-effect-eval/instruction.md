Seat the tabular uplift evaluation so `/app/scripts/run_uplift_eval.sh`
writes `/output/uplift-eval.json` inside the metric bands documented under
`/app/docs/uplift_bands.md`. Desk layout notes live in `/app/docs/desk_notes.md`.
Frozen outcomes sit under `/app/data/outcomes/`, treatments under
`/app/data/treat/`, features under `/app/data/feat/`, and the estimator
roster under `/app/data/estimators/`; evaluation preference and tip binding
live under `/app/calib/`.

The report carries a top-level schema_tag, a slices array, and an eval_ok
flag; field layout and the required slice set are documented in
`/app/docs/uplift_bands.md`. For each required slice, auuc and qini must meet
the published bands and must be the scored column that the estimator roster
assigns to the bound estimator. treatment_tip carries the epoch of the
durable assignment tip as a number, not a live observational tip and not a
tip id string. propensity must follow the durable estimator bound from that
tip. Evaluation stays in trial mode, and refreshes seating surfaces on every
engine build, until the calibration preference and the tip bind receipt under
`/app/calib/` both agree with the registry-resolved durable tip, so surface
edits alone do not stick. `/app/tools/upliftprobe` may print a stable-looking
status line during an unhealthy run. The verifier rebuilds `/app/eng` and
re-runs the eval on both the shipped materials and novel sealed tips;
hand-written reports fail. Two consecutive runs must be byte-identical.
