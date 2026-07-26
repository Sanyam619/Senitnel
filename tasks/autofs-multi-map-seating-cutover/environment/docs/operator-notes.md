Operator notes
==============

Seating is driven by `/app/ops/run_autofs_seat.sh`. Helpers under `/app/rim`,
`/app/ops`, `/app/bag`, and `/app/deck` prepare live state; `/app/bin/seatctl`
publishes the ledger when invoked by the emit step.

Surface `/usr/local/bin/autofshealth` only checks that drop-in and roster
paths exist. Do not treat a green surface probe as seating agreement.

Site-standard tokens for the folded effective policy are listed in
`/app/config/site_standard.conf`.

Optional helper path overrides (defaults match the live desk):
ABORT_D, PREF_D, ROSTER, AUTO_ROOT / ROOT, JOURNAL, STATE, EFF_POLICY, SEAT_OUT.
