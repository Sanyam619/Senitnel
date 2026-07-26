Operator notes
==============

Seating is driven by `/app/ops/run_gluster_seat.sh`. Helpers under
`/app/wire`, `/app/ops`, `/app/rim`, `/app/bag`, and `/app/deck` prepare the
live desk; `/app/bin/glusterseat` publishes the ledger when the emit step
invokes it.

What the shift log recorded after the window was interrupted: the draft
report disagrees with the durable authority on brick sets, on which
volumes are started, and on heal pending counts; and hand edits under
`/etc/glusterfs/` do not survive the next pass.

Surface `/usr/local/bin/glusterhealth` only checks that the brick sheet
directory and the roster exist. It ignores held bricks and may print
started while `seat_ok` is false. Do not treat a green surface probe as
seating agreement.

Optional helper path overrides (defaults match the live desk):
GLUSTER_ROOT, ROSTER, DROPIN_D, BRICK_D, LIVE_FLOORS, EFF_POLICY, SEAT_OUT,
SCAN_OUT.
