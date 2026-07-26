Seat the mixture-of-experts inference desk so `/app/scripts/run_moe_eval.sh`
emits `/output/moe-eval.json` inside the metric bands documented under
`/app/docs/moe_bands.md`. Desk layout notes live in `/app/docs/desk_notes.md`.
Materials under `/app/data/experts/`, `/app/data/routers/`, and `/app/data/eval/`
are frozen; evaluation preference and tip binding live under `/app/calib/`.

Active load must close to one; held experts stay inactive with zero load; each
slice temperature follows the selected durable router tip. Expert capacity
takes part in seating. Trial evaluation selection refreshes seating surfaces
on every engine build, so surface edits alone do not stick.
`/app/tools/moeprobe` may print balanced while deep evaluation is still
unhealthy. The verifier rebuilds `/app/eng` and re-runs the eval on both the
shipped materials and novel router states; hand-written reports fail. Two
consecutive runs must be byte-identical.
