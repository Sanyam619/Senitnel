Operator notes
==============

Run `/app/ops/run_path_seat.sh` to refresh the derived live tables under
`/var/lib/systemd/ops/live/` and publish `/output/path-seat.json`. The prebuilt
publisher `/app/publisher/pathseat` consumes those live tables plus the frozen
unit fixtures and writes the report. The surface probe
`/usr/local/bin/pathhealth` reads currently loaded units only; it does not
consult durable watch tips, generation floors, watch generations,
`DirectoryNotEmpty` exclusions, or trigger-journal continuity, so it can report
`WATCH-OK` while the deep arming state is wrong.

Abort residue lives under `/var/lib/systemd/ops/abort.d/<unit>.path.d/` and
rematerializes into the live drop-in `/etc/systemd/system/<unit>.path.d/90-local.conf`
on every seating pass unless `/var/lib/systemd/ops/state/cutover.ok` contains
`gen=<target>` matching `/var/lib/systemd/ops/state/generation.target` and
`mode=seal`. A matching receipt applies the site-standard drop-in tokens from
`/app/config/site_standard.conf` to that live drop-in; a stale or missing
receipt rematerializes the abort drop-in for that pass and the abort content
stays live. The abort package under `abort.d/` stays forensic. Scenario:
`generation.target` advances past the sealed `gen` recorded on the receipt, and
the next seating pass rematerializes abort into the live drop-in. Sealing the
cutover is a deliberate act — establish the receipt with the current
`generation.target` and `mode=seal`, and record the selected durable generation
in `/var/lib/systemd/ops/state/generation.live`.

Unit fixtures under `/app/data/pathunits/` are integrity-pinned by
`/app/packaging/pathunits.sha256` and include deploy-artifact, cert-bundle,
config-reload, spool-flush, cache-prime, and log-rotate. The prebuilt publisher
`/app/publisher/pathseat` is pinned in the same manifest and must not be edited.
Optional additional unit fixtures may appear under
`/var/lib/systemd/ops/extra/` (for example a `.meta` with a matching floor and
watch generation and a preference row) and must follow the same fold, tip,
arming, and trigger path.

Deep armed ownership lands at `/run/systemd/watch-seat/armed.map` as
`unit=<watched path>` lines, sorted, one per armed unit, after a successful
seating pass.
