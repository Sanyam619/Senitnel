Layout
======

Live desk
---------
- `/etc/nftables.conf` — base include of `/etc/nftables.d/`
- `/etc/nftables.d/*.nft` — rule fragments (lexical fold order)
- `/etc/nft/floors/` — live tip floor sheets (not durable authority)
- `/etc/nft/surface_prefer.conf` — surface policy sheet (not durable)

Durable ops
-----------
- `/var/lib/nft/ops/prefer.conf` — durable base-chain policies
- `/var/lib/nft/ops/journal.jsonl` — cutover journal
- `/var/lib/nft/ops/abort.d/` — abort fragment package; forensic copy at
  `/var/lib/nft/ops/abort.d/90-local.nft`
- `/var/lib/nft/ops/fold.nft` — folded ruleset after seating
- `/var/lib/nft/ops/applied.nft` — `nft list ruleset` dump
- `/var/lib/nft/floors/` — durable generation floors (`filter.floor`, `nat.floor`, `mangle.floor`, `raw.floor`)
- `/var/lib/nft/state/` — gen.target, gen.live, cutover.ok, clock

Fixtures
--------
- `/app/data/nft/` — frozen fragment templates (packaging-pinned)
- `/app/config/site_standard.conf` — operator memo only (`key=value`); not an
  nftables fragment body. Live `/etc/nftables.d/90-local.nft` must stay a real
  fragment without `abort_lab` (comment-only is fine).
- `/app/ops/run_nft_seat.sh` — seating entrypoint
