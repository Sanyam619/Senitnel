Seat the continual-learning evaluation so `/app/scripts/run_cl_eval.sh`
emits `/output/cl-eval.json` inside the metric bands documented under
`/app/docs/cl_bands.md`. Desk layout notes live in `/app/docs/desk_notes.md`.
Task fixtures under `/app/data/tasks/` and replay-buffer materials under
`/app/data/replay/` are frozen; evaluation preference and tip binding live
under `/app/calib/`.

The report carries a top-level schema_tag, a tasks array, and an eval_ok
flag; field layout and the required task set are documented in
`/app/docs/cl_bands.md`. Accuracy for each task should reflect replay drawn
from the sealed buffer tip and the tip-epoch hold window for that task's
stratum, not a live overflow buffer, a retired snapshot, or a coarse roster
that overstates holds. Forgetting should track a task's drop from its own
peak accuracy rather than a flat proxy. An earlier task's accuracy stays
inside its band after replay is correctly seated. Trial evaluation
selection refreshes seating surfaces on every engine build, so surface
edits alone do not stick.

When the verifier points the eval at an alternate data root that still has
journal and task fixtures, tip_epoch and replay_frac on every row must still
follow that root's journal-resolved sealed tip. Calib preference seats
rebuild durability; it does not replace the journal-resolved fraction on
those reports.

`/app/tools/clprobe` may print a stable-looking status line during an
unhealthy run. The verifier rebuilds `/app/eng` and re-runs the eval on
both the shipped materials and novel sealed tips; hand-written reports
fail. Two consecutive runs must be byte-identical.
