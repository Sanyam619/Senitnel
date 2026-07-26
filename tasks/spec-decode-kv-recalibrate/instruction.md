The speculative-decoding evaluation pipeline under `/app/eng` has
drifted off the non-speculative reference stream under
`/app/data/nonspec/`. Bring it back into agreement across every slice
under `/app/data/slices/` while preserving the acceptance rate
speculative decoding is supposed to deliver. Shortcuts that
short-circuit speculation are not acceptable — the verifier rejects
reports produced by collapsing the draft side onto the target,
bypassing hard positions, or hand-editing the report to disagree with
what the engine's own probe stream reconstructs.

Run everything through `/app/scripts/run_eval.sh`; it rebuilds the
engine and writes `/output/recalibration-report.json`. Leave the crate
under `/app/eng` rebuildable from source — later checks recompile those
sources rather than trusting a one-off binary swap. The report's
`schema_tag`, field layout, and the numeric health bands the report
must land in are documented in `/app/docs/metrics.md`. The runtime
protocol, the configuration tables under `/app/data/config/`, the
per-slice fixtures under `/app/data/slices/`, and the non-speculative
baseline under `/app/data/nonspec/` are described in
`/app/docs/protocol.md`. Do not modify anything outside `/app/eng`, and
do not touch the fixtures under `/app/data/`.

