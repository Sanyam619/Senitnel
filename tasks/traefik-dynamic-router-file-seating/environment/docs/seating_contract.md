Seating Contract
================

Graded seating produces `/output/traefik-seat.json`:

- `schema_tag` must be the literal string `traefik-seat-v1`
- `routers` lists every roster name with string `rule`, string `service`,
  integer `generation`, and boolean `active`
- `middlewares` lists every middleware name with string `type` and boolean
  `attached`
- `seat_ok` is true only when every roster router and middleware agrees with
  durable authority (defined below)

What "agrees with durable authority" means
-----------------------------------------

1. `rule` and `service` equal the durable journal tip for that name
2. `generation` equals the raw sealed-journal tip generation for that name
3. `active` is true only when that tip matches and generation ≥ durable floor
4. Middleware `attached` matches `/var/lib/traefik/ops/mw_prefer.toml`
5. Live drop-in policy, cutover receipt, gen.live, and forensic abort.d match
   the cutover rules below

Tip journal
-----------

`/var/lib/traefik/ops/journal.jsonl` records tip rows. The serving tip is the
newest durable tip that is not listed in `retired_tips.jsonl`. Live-only tip
rows are not selected. After apply, `gen.live` equals `gen.target` and each
`tip_<name>.gen` matches the selected tip generation for that name.

Prefer and binding
------------------

Durable selection preference and tip binding under `/var/lib/traefik/ops/`
gate whether surface materials under `ops/seeds/` overwrite live dynamic
router sheets on each seating pass. Until preference is durable authority
and the binding names the resolved serving tip, surface seeds rematerialize
over naive live edits.


Activity and floors
-------------------

Durable floors under `/var/lib/traefik/ops/floors/<name>.floor` are operator
policy. A tip below its durable floor is still reported in
`routers[].generation` and must set `active=false`. Live sheets under
`/etc/traefik/floors/` are not the durable authority.

Middleware
----------

`middlewares[].attached` follows durable `mw_prefer.toml` (`attach.<name>=true|false`).
Live `/etc/traefik/dynamic/40-middlewares.yml` may show a different chain.

Abort and cutover
-----------------

Abort-window residue under `/var/lib/traefik/ops/abort.d/` rematerializes into
live dynamic/ on every seating pass unless
`/var/lib/traefik/ops/state/cutover.ok` exists as plain `key=value` lines with
exactly `gen=<target>` (matching `gen.target`) and `mode=seal`. A matching
receipt skips rematerialize; it does **not** mean delete the live drop-in.
`/etc/traefik/dynamic/90-local.yml` must remain present and carry site-standard
tokens from `/app/config/site_standard.yml`. The abort package itself stays
forensic. A later abort fragment that marks routers revoked must not survive
into the graded active flags for correctly seated routers.

Idempotency
-----------

Two seating runs must leave `/output/traefik-seat.json` byte-identical.
