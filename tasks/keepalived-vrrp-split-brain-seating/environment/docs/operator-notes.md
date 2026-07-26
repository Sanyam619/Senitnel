Operator notes
==============

Run `/app/ops/run_vrrp_seat.sh` to refresh live tables under
`/var/lib/keepalived/ops/live/` and publish `/output/vrrp-seat.json`. The
prebuilt publisher `/app/publisher/vrrpseat` consumes those live tables plus frozen
peer fixtures. Surface `/usr/local/bin/vrrphealth` reads current MASTER tokens
only and does not consult durable preference, holds, floors, track probes,
netif generations, or transition continuity.

Abort residue under `/var/lib/keepalived/ops/abort.d/90-local.conf` copies into
live `/etc/keepalived/conf.d/90-local.conf` on every seating pass unless
`/var/lib/keepalived/ops/state/cutover.ok` contains `gen=<target>` matching
`generation.target` and `mode=seal`. Matching receipts skip rematerialize; they
do not delete the live drop-in. The abort package stays forensic. Site-standard
tokens from `/app/config/site_policy.conf` belong on the live drop-in under a
matching seal receipt. A stale or missing receipt rematerializes abort into live,
and that abort content stays for the pass; site-standard does not replace abort
on a mismatch. Scenario: `generation.target` advances past the sealed `gen` on
the receipt — the next seating pass rematerializes abort and leaves those tokens
live. A successful seating pass writes the receipt itself with the current
`generation.target` and `mode=seal`, and records the selected durable generation
in `/var/lib/keepalived/ops/state/generation.live`.

Peer fixtures under `/app/data/vrrp/` are integrity-pinned by
`/app/packaging/vrrp.sha256` and include peer_a, peer_b, peer_c, peer_d,
peer_e, and peer_f. The prebuilt publisher `/app/publisher/vrrpseat` is pinned
in the same manifest and must not be edited. Optional additional peer sheets may
appear under `/var/lib/keepalived/ops/extra/` (for example peer_g.conf with a
matching floor and netif generation) and must follow the same fold, track,
eligibility, and election path when preference rows name them.

Deep VIP advertise rows land at `/etc/keepalived/runtime/advert.map` as
`vip=peer` lines after a successful seating pass.
