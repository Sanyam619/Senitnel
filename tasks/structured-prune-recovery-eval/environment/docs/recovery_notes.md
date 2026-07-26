# Recovery desk notes

## What the desk publishes

`/app/scripts/run_prune_eval.sh` rebuilds the evaluation workspace under
`/app/eng` and publishes `/output/prune-eval.json`. The report has one entry per
scenario on the published roster, and the roster is the one the desk ships
under `/app/data/eval/roster.txt`.

## Frozen material

Everything under `/app/data/` is frozen: the dense snapshots, the channel
rosters, the registry, the calibration rows, the evaluation slices and the
block layout in `/app/data/arch/topology.txt` the stack is built from. The
published numbers have to come from running those snapshots over those slices.
The desk keeps a pre-freeze archive snapshot beside the two it scores; nothing
is published from it.

## Scenarios

A scenario names a starting point and a slice. A `cold_*` scenario starts from
the frozen dense snapshot. A `resume_*` scenario starts from the mid-run
snapshot of the same dense run. The two snapshots carry the same weights, so a
`cold_*` scenario and its `resume_*` partner are two starting points for one
measurement and are expected to publish the same accuracy.

The mid-run snapshot also records which generation it was taken under and the
per-channel statistics the dense run was carrying when it was written. Those
fields describe that dense run, not the scoring pass that publishes numbers
today.

## Channel rosters

Rosters live in `/app/data/masks/`. Each sheet names its generation, its kind
and, per block, the channels that survive. The registry says which generations
exist: `/app/data/mask_registry/tip_journal.jsonl` carries one row per
generation with the state it reached, and
`/app/data/mask_registry/retired_tips.jsonl` names generations that were rolled
back after the fact. Rows are appended in the order the desk saw them, which is
not the order of their generation numbers.

A generation reaches `durable` once its roster has been accepted for scoring.
A `staged` row is a proposal: the live overlay sheet the reshape tooling keeps
writing is one of those. Sheets also carry a kind. Published numbers are scored
on the durable structured generation the registry resolves; overlay proposals
and unstructured trial sheets are not scoring rosters even when they look new.

## Re-fitting

Dropping channels leaves the remaining stack's normalisation and the classifier
out of line with the frozen snapshot. Both have to be brought back into line
against the calibration material for a scenario before that scenario is scored.
Accuracy only lands inside the published bands when that re-fitting matches the
surviving stack the roster actually leaves.

## Seating the workspace

The workspace re-seats parts of itself from its own seed material on every
rebuild until the acceptance receipt in `/app/serving/bind.accept` agrees with
the registry. The receipt records whether this is a scoring pass, which
generation the desk is bound to, that generation's number, and how many
channels its roster keeps in total. Until the receipt describes a generation
the registry will actually score under, the rebuild announces that it re-seated
and the workspace scores under its seed seating. `/app/calib/eval_pass.toml`
is a desk note, not the seating authority.

## Health view

`/app/data/fixtures/surface_ok.json` is a captured sweep from an earlier
session, kept for eyeballing shapes. It reports healthy numbers regardless of
what the current report contains, and nothing is published from it.
