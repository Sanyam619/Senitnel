Seating notes
=============

The rollout of the mesh generation named in
`/var/lib/consul/ops/state/generation.target` was aborted part way through.
Operations kept the local drop-in it had at that moment in
`/var/lib/consul/ops/abort.d/90-local.hcl` so the window could be reconstructed
later. That package seats `alpha` on `node-a9` and `beta` on `node-b9` and
carries the `prefer_abort` tip policy of the aborted window.

Rollback residue copies back into live `/etc/consul.d/conf.d/90-local.hcl` on
every seating pass unless `/var/lib/consul/ops/state/cutover.ok` carries
`gen=<generation.target>` and `mode=seal`. A matching receipt skips that copy;
it does not delete the live drop-in, and the rollback package stays where it is.
Under a matching receipt the live local drop-in carries the site-standard tokens
from `/app/config/site_standard.conf`. A stale or missing receipt leaves the
rollback bindings live for that pass, and site-standard tokens do not displace
them while the receipt does not match.

Scenario: `generation.target` advances past the generation on the receipt, and
the next pass seats the rollback bindings again until a pass records the new
seal.

A completed seating pass records the receipt itself with the current
`generation.target` and `mode=seal`, and records the generation of the batch it
selected in `/var/lib/consul/ops/state/generation.live`.

The published ledger at `/output/consul-seat.json` is rewritten from the work
tables on every pass, so hand-written ledgers do not survive a pass. Two passes
over unchanged materials leave the ledger byte-identical.
