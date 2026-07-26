Publish a held-out contrastive vision–language retrieval evaluation for the
frozen image and caption banks so `/app/scripts/run_vl_eval.sh` writes
`/output/vl-eval.json` inside the recall bands in `/app/docs/vl_bands.md`.
The report carries top-level `schema_tag` (`vl-eval-v1`), a `slices` array,
and `eval_ok`. Field layout and the required slice set are in
`/app/docs/report_schema.md`. Evaluation notes live in
`/app/eval/runbooks/eval_notes.md`. Image banks under `/app/data/images/` and
caption query frames under `/app/data/captions/` stay frozen, as do schedules
and the tip journal under `/app/data/`. Evaluation selection and tip binding
live under `/app/calib/`.

Every required slice must sit inside its published recall@5 and recall@10
band with `eval_ok` true. Each resume slice must reproduce its cold twin
within `1e-4`. `temperature` must equal the durable logit-scale tip schedule
row; `pool` must be the durable negative-pool preference (`inbatch` or
`hardmine`), not the surface decoy; `tip_epoch` must equal the sealed bank
tip generation. Retired tips and live shadow-bank tips are not the bound tip.
Mixed slices score against the image-bank composition that tip declares.

While trial evaluation preference stays armed, or the tip bind receipt does
not match the registry-resolved tip, a refreshed evaluation run restores
seating surfaces from the desk seed set. Corrections in those surfaces do not
stick until selection and tip binding are publishable together.

`/app/tools/vlprobe` may report aligned while deep evaluation is still
unhealthy — it scores train-set overlap only. The verifier re-invokes the
VL entrypoint on the shipped materials and on a novel durable tip;
hand-written reports fail. Two consecutive entrypoint runs must be
byte-identical. `/app/data/fixtures/surface_ok.json` is a stale surface-sweep
artifact (including an inbatch pool seating) and is not an authority.
`/app/data/ledger/` is a leftover sweep ledger and is not the tip-journal
authority.
