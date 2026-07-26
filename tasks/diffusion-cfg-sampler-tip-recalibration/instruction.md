The diffusion evaluation engine under /app scores frozen banks against
checkpoints and publishes a health report. The report is currently out of
agreement with the published metric bands. Recalibrate the evaluation so the
published report is healthy and verifiable.

Publish with /app/scripts/run_diff_eval.sh, which rebuilds the workspace and
writes /output/diff-eval.json. The report carries a top-level schema_tag
string, a scenarios array, and a bands_ok flag; field layout and the required
scenario set are documented in /app/docs/report_schema.md. Published health
bands live in /app/docs/diff_bands.md. Evaluation notes live in
/app/eval/runbooks/eval_notes.md. Evaluation selection and tip binding state
live under /app/calib/. Banks, schedules, checkpoints, and the tip journal
under /app/data/ are frozen inputs.

Required scenario ids are cold_a, resume_a, cold_b, resume_b, mix_c, and
mix_d. Every scenario must sit inside its published band with bands_ok true.
Each resume scenario must reproduce its cold twin: fid and clip_score agree
within 1e-4. Resume checkpoints store block-packed VAE frames; unpacking must
reproduce the cold-run geometry. tip_epoch must equal the durable tip
generation the evaluation binds for the run — retired tips and live sweep tips
are not the bound tip. cfg_scale and sampler must be the durable schedule pair
for that tip. Mixed scenarios are scored against the segment composition that
tip declares.

While trial evaluation preference stays armed, or the tip bind receipt does
not match the registry-resolved tip, a rebuild restores seating surfaces from
the desk seed set. Source corrections in those surfaces do not survive a
rebuild until selection and tip binding are publishable together.

The verifier re-runs the entrypoint and requires the re-published report to be
byte-identical to /output/diff-eval.json; hand-written or template reports
fail. Two consecutive entrypoint runs must be byte-identical. The verifier
also injects a novel durable tip and expects tip_epoch, cfg_scale, sampler,
and mix metrics to move with that tip. Everything under /app/data/ is frozen
input. /app/docs/diff_bands.md is the published contract and is also frozen.

/app/data/fixtures/surface_ok.json is a stale display artifact from the last
surface sweep. It can look healthy while the desk is not — including a short
teacher-forced sampler seating. The desk never reads it, and reports that copy
its numbers fail verification. /app/data/ledger/ is a leftover sweep ledger
and is not the tip-journal authority the desk binds against.
