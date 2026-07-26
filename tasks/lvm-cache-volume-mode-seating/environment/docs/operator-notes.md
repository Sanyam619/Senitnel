Operator notes
==============

Seating is driven by `/app/ops/run_lvmcache_seat.sh`. Helpers under
`/app/wire`, `/app/ops`, `/app/rim`, `/app/bag`, and `/app/deck` prepare the
live desk; `/app/bin/cacheseat` publishes the ledger when the emit step
invokes it.

What the shift log recorded after the window was interrupted: the draft
report disagrees with the durable authority on cache modes, on which
volumes are attached, and on the maintenance windows; and hand edits under
`/etc/lvm/` do not survive the next pass.

Surface `/usr/local/bin/lvmhealth` only checks that the cache sheet
directory and the roster exist. Do not treat a green surface probe as
seating agreement.

Optional helper path overrides (defaults match the live desk):
LVM_ROOT, ROSTER, DROPIN_D, SHEET_D, LIVE_FLOORS, EFF_POLICY, SEAT_OUT,
SCAN_OUT.
