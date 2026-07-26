Live Traefik file-provider seating under `/etc/traefik/` and
`/etc/traefik/dynamic/` drifted from durable route authority under
`/var/lib/traefik/ops/`. Surface `/usr/local/bin/traefikhealth` may print
`routed` while deep seating is wrong. Frozen fixtures under
`/app/data/traefik/` are integrity-pinned; do not rewrite them. Operator
seating starts at `/app/ops/run_traefik_seat.sh`. Docs under `/app/docs/`
expand journals, prefer sheets, abort folds, and seating scenarios.

Write `/output/traefik-seat.json` with schema_tag, routers, middlewares, and
seat_ok. Each routers entry carries name, rule, service, generation, and
active. Each middlewares entry carries name, type, and attached.
schema_tag must be traefik-seat-v1.

Scenarios the desk must satisfy:

- A router is active only when its rule and service match the durable
  journal tip and that tip's generation is at or above the durable floor
  (equality inclusive). Below-floor tips are still reported; they are not
  active.
- Middleware attached flags follow the durable prefer sheet, not the live
  decoy chain under `/etc/traefik/dynamic/`.
- Abort-window residue under `/var/lib/traefik/ops/abort.d/` rematerializes
  into `/etc/traefik/dynamic/` on every seating pass unless
  `/var/lib/traefik/ops/state/cutover.ok` matches the generation target with
  mode=seal as plain `key=value` lines. A matching receipt skips
  rematerialize; it does not delete the live drop-in. The abort package
  stays forensic. Site-standard tokens from `/app/config/site_standard.yml`
  apply to live `/etc/traefik/dynamic/90-local.yml` under a matching seal
  receipt. A later abort fragment under that directory must not revoke a
  correctly seated router.
- seat_ok is true only when the ledger agrees with durable authority on
  every roster router and middleware. Two seating runs must leave
  `/output/traefik-seat.json` byte-identical.
