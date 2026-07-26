Publish a trustworthy held-out cross-encoder rerank evaluation for the frozen
candidate pools and qrels so `/app/scripts/run_rerank_eval.sh` writes
`/output/rerank-eval.json` inside the metric bands in `/app/docs/rerank_bands.md`.
The report carries top-level `schema_tag` (`rerank-eval-v1`), a `slices` array,
and `eval_ok`. Field layout and the required slice set are in
`/app/docs/report_schema.md`. Evaluation notes live in
`/app/eval/runbooks/eval_notes.md`. Pools and qrels under `/app/data/pools/` and
`/app/data/qrels/` stay frozen, as do score packs, schedules, and the tip journal
under `/app/data/`. Evaluation selection and tip binding live under `/app/calib/`.

Every required slice must sit inside its published nDCG@10 and MRR band with
`eval_ok` true. Each resume slice must reproduce its cold twin within `1e-4`.
`temperature` must equal the durable calibration tip schedule row; `fusion`
must be the durable mode (`rrf`, `linear`, or `learned`), not the surface
decoy; `tip_epoch` must equal the bound durable tip generation. Retired tips
and live sweep tips are not the bound tip. Mixed slices score against the
candidate-pool composition that tip declares.

While trial evaluation preference stays armed, or the tip bind receipt does
not match the registry-resolved tip, a refreshed evaluation run restores
seating surfaces from the desk seed set. Corrections in those surfaces do not
stick until selection and tip binding are publishable together.

`/app/tools/rerankprobe` may report pass while deep evaluation is still
unhealthy — it scores first-stage retrieval only. The verifier re-invokes the
rerank entrypoint on the shipped materials and on a novel durable tip;
hand-written reports fail. Two consecutive entrypoint runs must be
byte-identical. `/app/data/fixtures/surface_ok.json` is a stale surface-sweep
artifact (including a linear fusion seating) and is not an authority.
`/app/data/ledger/` is a leftover sweep ledger and is not the tip-journal
authority.
