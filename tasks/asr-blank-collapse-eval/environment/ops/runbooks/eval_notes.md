# Evaluation desk notes

## Inputs

`/app/data/audio/` holds per-utterance frame posteriors, one file per utterance
per slice. `/app/data/align/` holds the reference alignments for the same
utterances. `/app/data/lexicon/tokens.txt` maps unit indices to words; index 0
is the null unit. `/app/data/lm/bigram.bin` is the conditioning table used for
shallow fusion during search, and `/app/data/predict/bias.bin` is the
prediction-state table the joined path conditions on. All of these are frozen.

## Decoder registry

`/app/data/decoder_registry/tip_journal.jsonl` records decoder generations. A
generation is either `live` (staging entry, still being swept, may be rewritten
without notice) or `sealed` (frozen, reproducible). `retired_tips.jsonl` beside
it lists generations that were withdrawn after sealing; a withdrawn generation
stays in the journal for audit but is no longer eligible for a published pass.
The journal is appended in the order rows arrived at the desk, not in
generation order.

Each generation carries the fusion sheet it was measured on and the decode path
it was sealed with. `/app/data/fusion/table_h4.toml` and `table_k9.toml` hold
the shallow-fusion weights measured on each sheet, keyed by generation. Sheets
also hold rows for generations that have not been sealed yet, so a row existing
does not make it the row for this run.

## Desk state

`/app/calib/eval_pass.toml` records which pass the desk is running and
`/app/calib/decoder_selection.txt` records the generation the workspace is
seated against. The workspace under `/app/eng` restores its own seed seating
during a rebuild while the desk is not on a scoring pass or while the recorded
selection disagrees with the registry, so search changes only survive a rebuild
once the desk state agrees with the registry.

## Surfaces that are not authority

`/app/tools/asrprobe` is a fast health view. It reports on the captured sweep in
`/app/data/fixtures/probe_ok.json` using a greedy no-fusion read, which is why
it can report pass while a published run is nowhere near its bands.
`/app/data/sweep/legacy_runs.jsonl` is pre-freeze history kept for reference; it
was captured before the current alignments landed and is not comparable to the
published bands.
