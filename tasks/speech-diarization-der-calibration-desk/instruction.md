Seat the speaker-diarization evaluation so `/app/scripts/run_diar_eval.sh`
writes `/output/diar-eval.json` inside the metric bands documented under
`/app/docs/diar_bands.md`. Desk layout notes live in `/app/docs/desk_notes.md`.
Frozen audio sits under `/app/data/audio/`, RTTM references under
`/app/data/rttm/`, and evaluation preference with tip binding live under
`/app/calib/`.

The report carries a top-level schema_tag, a slices array, and an eval_ok
flag; field layout and the required slice set are documented in
`/app/docs/diar_bands.md`. For each required slice, der and jer must meet
the published bands. clustering must equal the durable method tip
(`ahc`, `spectral`, or `nme`) and must not follow the live decoy.
tip_epoch must carry the epoch of the sealed embedding-bank tip as a
number, not a tip id string. Evaluation stays in trial mode, and refreshes
seating surfaces on every engine build, until the calibration preference
and the tip bind receipt under `/app/calib/` both agree with the
registry-resolved durable tips, so surface edits alone do not stick.
`/app/tools/diarprobe` may print a low-DER status line that uses oracle
speaker counts while eval_ok stays false. The verifier rebuilds `/app/eng`
and re-runs the eval on both the shipped materials and novel sealed tips;
hand-written reports fail. Two consecutive runs must be byte-identical.
