Layout
======

Live file provider
------------------
- `/etc/traefik/traefik.yml` — static provider pointer
- `/etc/traefik/dynamic/` — dynamic router, middleware, and local drop-in sheets
- `/etc/traefik/floors/` — live floor sheets (not durable authority)

Durable ops
-----------
- `/var/lib/traefik/ops/prefer.toml` — selection preference
- `/var/lib/traefik/ops/tip_bind.accept` — tip binding record
- `/var/lib/traefik/ops/journal.jsonl` — route tip journal
- `/var/lib/traefik/ops/retired_tips.jsonl` — retired tip ids
- `/var/lib/traefik/ops/mw_prefer.toml` — middleware attachment prefer
- `/var/lib/traefik/ops/floors/` — durable generation floors
- `/var/lib/traefik/ops/abort.d/` — abort-window residue package
- `/var/lib/traefik/ops/seeds/` — surface rematerialize materials
- `/var/lib/traefik/ops/state/` — gen.target, gen.live, cutover.ok, tip_*.gen

Fixtures and entry
------------------
- `/app/data/traefik/` — frozen router fixtures
- `/app/ops/run_traefik_seat.sh` — seating entrypoint
- `/usr/local/bin/traefikhealth` — surface status helper
