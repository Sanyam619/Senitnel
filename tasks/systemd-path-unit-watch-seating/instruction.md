Live systemd path-unit seating under `/etc/systemd/system/` and durable
operations state under `/var/lib/systemd/ops/` drifted following a watch-tip
cutover. Surface `/usr/local/bin/pathhealth` may print WATCH-OK with deep
arming wrong. Frozen unit fixtures under `/app/data/pathunits/` are
integrity-pinned; do not rewrite them. The prebuilt publisher
`/app/publisher/pathseat` is also integrity-pinned and must not be modified.
Operator seating starts at `/app/ops/run_path_seat.sh` and publishes through
that publisher. Docs under `/app/docs/` expand the unit fold, journals,
floors, and seating scenarios.

Write `/output/path-seat.json` with schema_tag, paths, triggers, and seat_ok.
Each paths entry carries unit, path_exists, path_changed, generation, and
armed. Each triggers entry carries unit, last_epoch, and honored. schema_tag
must be path-seat-v1.

Scenarios the desk must satisfy:

- Effective PathExists and PathChanged for a unit come from the full lexical
  fold of the base `.path` plus `.path.d/*.conf` drop-ins. The unit generation
  is its per-unit tip from the authoritative durable batch.
- Preference tips come from the latest sealed and complete durable batch.
  Incomplete later batches are not selected. The generation of that selected
  batch is written to `/var/lib/systemd/ops/state/generation.live`.
- Arming requires folded watched paths that match the durable tip, tip at or
  above the unit floor, watch generation at or above that same floor, and no
  DirectoryNotEmpty watch on the unit. A DirectoryNotEmpty bait unit stays
  unarmed with a matching PathExists.
- A trigger entry exists for a unit with an unretracted fire in the trigger
  journal; last_epoch is that unit's latest unretracted fire epoch.
  Retractions cancel the matching event id only. A trigger is honored for an
  armed unit only.
- Abort residue under `/var/lib/systemd/ops/abort.d/` rematerializes into
  live `.path.d` on every seating pass unless `/var/lib/systemd/ops/state/cutover.ok`
  matches the generation target with mode=seal. A matching receipt skips
  rematerialize; it does not delete the live drop-in. The abort package stays
  forensic. Site-standard tokens from `/app/config/site_standard.conf` apply to
  live `/etc/systemd/system/deploy-artifact.path.d/90-local.conf` under a
  matching seal receipt. A stale or missing receipt rematerializes abort into
  the live drop-in for that pass; site-standard tokens do not override abort on
  a mismatch.
- Deep armed ownership is recorded under `/run/systemd/watch-seat/armed.map`,
  one `unit=<watched path>` line per armed unit, sorted. Surface loaded maps
  are not durable authority.
- seat_ok is true only if the ledger agrees with durable authority and the
  floor, watch-generation, and DirectoryNotEmpty rules. Two seating runs must
  leave `/output/path-seat.json` byte-identical.
