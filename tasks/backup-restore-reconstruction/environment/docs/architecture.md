Architecture
============

Crash exports under `/app/data/episodes/` are immutable. Live fleet
administration lives under `/etc/fleet`, `/var/lib/fleet`, and
`/var/run/fleet`.

Layout
------
- `/etc/fleet/reconcile.d/*.conf` — drop-in fragments; lexical fold builds
  effective `/etc/fleet/reconcile.conf`
- `/etc/fleet/site_standard.conf` — site reference tokens
- `/etc/fleet/fleetd.env` — supervisor tokens including `PAYLOAD_LINEAGE`
  (volume subdirectory name such as `sealed`, not the journal mode token
  `seal`), `HOLD_TOKEN`, `FLEET_VOLUME_ROOT`, `FLEET_RUNTIME_ROOT`
- `/var/lib/fleet/ops/journal.jsonl` — durable cutover / rollback journal
  (seeded from `/app/ops/journal.seed.jsonl`; override path via `FLEET_JOURNAL`
  if set)
- `/var/lib/fleet/ops/abort.d/` — abort-window drop-in residue rematerialized
  unless `/var/lib/fleet/state/cutover.ok` matches the sealed cutover; the
  abort package keeps its synonym tokens (do not rewrite it to site-standard)
- `/etc/fleet/reconcile.d/90-local.conf` — live local drop-in; must stay
  present with site-standard tokens once cutover is armed (rewrite live
  synonyms in place; do not delete it to “suppress” abort residue)
- `/var/lib/fleet/state/cutover.ok` — durable receipt as `key=value` lines
  (`gen=`, `hold=`, `mode=seal`), not JSON
- `/var/lib/fleet/state/gen.target`, `gen.live`, `attach.intent`, `hold.token`
- `/var/lib/fleet/volumes/<episode>/{sealed,decoy}/`
- `/var/lib/fleet/runtime/<episode>/payload.bin` (+ `.hold`)
- `/var/lib/fleet/leases/<episode>.json` (e.g. `beta.json`, `epsilon.json`)
- `/var/run/fleet/gate/<episode>/<peer>`
- `/var/log/fleet/` — host ops logs (recovery may write under
  `/var/log/fleet/recovery`)

Toolchain
---------
- Prebuilt `fleetctl` / `yarder` / `fleetpeek` under `/app/bin/` (restore
  copies under `/usr/lib/fleet/bin/`). `fleetctl` requires fleetd's pidfile
  and reads live policy / leases / gates / runtime payloads.
- `/app/ops/run_recovery.sh` orchestrates admin helpers, starts fleetd, and
  runs prebuilt `fleetctl`. It does not rebuild from source.
- `/app/ops/fleethealth` is a surface probe only.

Stale copies under `/app/config/reconcile.conf` are packaging leftovers.
Live drop-ins are under `/etc/fleet/reconcile.d/`.
