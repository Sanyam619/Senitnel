NFSv4.2 Site Recovery Lab
=========================

Lab host for rehearsing post-reboot recovery of a site NFSv4.2 server
after unclean restarts. Captured reboot episodes live under
`data/episodes/`. Operator documentation is under `docs/`.

Layout
------
- `include/`, `lib/`, `tools/` — on-host recovery sources
- `bin/` — built operator binaries (`nfsr-inspect` ships with the image)
- `data/` — per-reboot episode journals (do not modify during recovery)
- `ops/` — operator scripts for the recovery pass
- `docs/` — recovery semantics and report contract
- `config/` — site recovery policy
- `packaging/` — pinned digests for shipped binaries

Operator notes
--------------
`make bin/nfsr-inspect` builds the inspector.

`ops/run_recovery.sh` rebuilds and runs the site recovery pass against
every episode under `data/episodes/`, writing `/output/reconciliation.json`.

`nfsr-inspect <episode-dir>` prints a summary of each journal file in
that episode directory (server reclaim log, per-client op logs, copy
intent record, namespace snapshot).
