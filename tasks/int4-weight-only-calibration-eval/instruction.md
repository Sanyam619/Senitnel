# Bring the INT4 weight-only evaluation into its published bands

The evaluation desk under `/app/eng` scores a four-bit weight-only
quantization of a frozen classifier and publishes, for every scenario, the
perplexity and top-1 agreement it reaches, the grouping width it quantized
under and the registry generation it scored against. The perplexities it
publishes now sit outside the documented bands, the grouping width it reports
is the one on the live per-channel sheet rather than on a generation the desk
scores under, and every scenario is quantized under a scale sheet that was
captured by an earlier revision of the calibration desk instead of one measured
on this pass.

Bring the published evaluation into the documented bands.
`/app/scripts/run_int4_eval.sh` publishes `/output/int4-eval.json` carrying
`schema_tag`, `scenarios` and `bands_ok`; the report shape is described in
`/app/docs/report_schema.md`, the bands in `/app/docs/int4_bands.md` and the
desk outcomes in `/app/docs/quant_notes.md`. Every scenario on the roster has
to land inside both of its bands, each cold scenario and its resume partner
have to agree to within `1e-4`, the grouping width and generation number a
scenario reports have to be those of the generation it was scored under rather
than the live per-channel sheet, and the per-input-channel scales have to be
measured on the calibration rows that generation admits.

The FP16 snapshots, the captured scale banks, the calibration rows, the
quantization registry, the grouping sheets, the evaluation slices and the layer
layout under `/app/data/` are inputs, not outputs, and so are the published
bands. The workspace under `/app/eng` is rebuilt from its own sources and the
entrypoint is re-run, so a report that only exists as a published file does not
survive; two consecutive runs must publish byte-identical reports, and a
registry generation that has not been seen before must move the report with it.
`/app/data/fixtures/surface_ok.json` is a captured sweep — it reports healthy
numbers while the published report is outside its bands.
