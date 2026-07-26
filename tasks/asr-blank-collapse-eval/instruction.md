# Seat the speech recognition evaluation desk

The desk publishes word- and character-error rates for six frozen speech
slices, and the rates it publishes are nowhere near the published acceptance
bands. The configuration the report describes alongside them — decode path,
shallow-fusion weight, and decoder registry generation — does not agree with
the registry the desk scores against either.

Seat the desk so a published pass reproduces the documented evaluation.

`/app/scripts/run_asr_eval.sh` publishes `/output/asr-eval.json`, carrying
`schema_tag`, a `slices` array, and `eval_ok`; per-slice fields are described
in `/app/docs/report_schema.md`. Every required slice has to land inside its
bands in `/app/docs/asr_bands.md`, the configuration a slice reports has to be
the one the bound decoder generation carries, and the report has to come out
clean.

Frame posteriors under `/app/data/audio/`, reference alignments under
`/app/data/align/`, the lexicon, the conditioning and prediction tables, the
fusion sheets, the decoder registry, and the published bands are frozen inputs.
The published rates have to come from decoding those posteriors against those
alignments. Reference material for the desk sits under `/app/docs/` and
`/app/ops/runbooks/`.

The evaluation workspace under `/app/eng` is rebuilt from its own sources and
the entrypoint is re-run, so a report that only exists as a published file does
not survive. Two consecutive entrypoint runs must publish byte-identical
reports, and a registry generation that has not been seen before must move the
report with it rather than leave the previous numbers standing.

`/app/tools/asrprobe` is a health view over a captured sweep; it reports pass
while the published report is outside its bands.
