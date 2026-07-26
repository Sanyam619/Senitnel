Seat the preference-alignment evaluation desk so `/app/scripts/run_pref_eval.sh`
emits `/output/pref-eval.json` inside the win-rate bands and KL ceilings in
`/app/docs/pref_bands.md`. Desk layout notes live in `/app/docs/desk_notes.md`.
Frozen preference pairs sit under `/app/data/prefs/`, the reference policy under
`/app/data/ref/`, the candidate under `/app/data/policy/`, and tip materials
under `/app/data/tips/`. Evaluation preference and tip binding live under
`/app/calib/`.

Each required slice must land inside its win-rate band while `kl_to_ref` stays
at or under the published ceiling. The reported `beta` must equal the durable
KL tip, and `tip_epoch` must equal the sealed journal tip — not the live
high-beta tip. Trial evaluation selection refreshes seating surfaces on every
engine build; surface edits alone do not stick. `/app/tools/prefprobe` may
print a high win rate while deep evaluation is still unhealthy. The verifier
rebuilds `/app/eng` and re-runs the eval on the shipped materials and on novel
tip states; hand-written reports fail. Two consecutive runs must be
byte-identical.
