# Embedding bank temperature recalibration

The retrieval evaluation desk under /app scores frozen contrastive embedding
banks against query checkpoints and publishes a health report. The report is
currently out of agreement with the published metric bands. Recalibrate the
evaluation so the published report is healthy and verifiable.

Publish the report with /app/scripts/run_embed_eval.sh, which rebuilds the
workspace and writes /output/embed-eval.json. The report carries a top-level
schema_tag string, a scenarios array, and a bands_ok flag; field layout and
the required scenario set are documented in /app/docs/report_schema.md. The
published health bands live in /app/docs/embed_bands.md. Desk behavior notes
live in /app/ops/runbooks/eval_notes.md. Evaluation selection and tip binding
state live under /app/calib/. Banks, checkpoints, the feature registry, and
scale tables under /app/data/ are frozen inputs.

## Graded outcomes

- Every scenario sits inside its published band and the report declares
  bands_ok true.
- Each resume scenario reproduces its cold twin: retrieval recall and
  clustering agreement match within 1e-4. Resume checkpoints store
  block-packed frames; unpacking must reproduce the cold-run embedding
  geometry.
- Temperature and bank_epoch follow the durable feature-registry tip that the
  evaluation binds for the run. Retired tips and live sweep tips are not the
  bound tip. Mixed scenarios are scored against the segment composition that
  tip declares.
- While trial evaluation preference stays armed, or the tip bind receipt does
  not match the registry-resolved tip, a rebuild restores seating surfaces
  from the desk seed set. Source corrections in those surfaces do not survive
  a rebuild until selection and tip binding are publishable together.
- The verifier re-runs the entrypoint and requires the re-published report to
  be byte-identical to /output/embed-eval.json; hand-written or template
  reports fail. Two consecutive entrypoint runs must be byte-identical. The
  verifier also injects a novel durable registry tip and expects temperature,
  bank_epoch, and mix metrics to move with that tip.
- Everything under /app/data/ is frozen input. /app/docs/embed_bands.md is the
  published contract and is also frozen.

## Notes

- /app/data/fixtures/surface_ok.json is a stale display artifact from the
  last surface sweep. It can look healthy while the desk is not. The desk
  never reads it, and reports that copy its numbers fail verification.
- /app/data/ledger/ is a leftover sweep ledger and is not the feature-registry
  authority the desk binds against.
