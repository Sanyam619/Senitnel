Layout
======

/app/ops/run_nspawn_seat.sh     seating entrypoint
/app/docs/                      seating contract and operator notes
/app/config/site_standard.conf  site-standard drop-in tokens
/app/data/machines/             frozen image fixtures (do not rewrite)
/etc/systemd/nspawn/            live .nspawn units and decoy sheets
/etc/systemd/nspawn/effective.conf   folded preference policy after seating
/etc/systemd/system/machines.target.wants/   live preference drop-ins
/var/lib/machines/images/       durable image tips
/var/lib/machines/live/         live shadow roots (non-authoritative)
/var/lib/machines/volumes/      sealed bind objects
/var/lib/machines/floors/       durable generation floors
/var/lib/machines/ops/          journal, ports, abort package
/var/lib/machines/ops/abort.d/90-local.conf   forensic abort residue
/var/lib/machines/state/        tip/elig stamps, cutover receipt, clock
/var/run/machines/              runtime stamps from seating passes
/var/run/machines/seat_first.bin   first-pass ledger bytes (verifier staging)
/var/run/machines/seat_second.bin  second-pass ledger bytes (verifier staging)
/output/nspawn-seat.json        seating ledger
