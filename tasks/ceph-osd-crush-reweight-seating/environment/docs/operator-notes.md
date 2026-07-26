# Operator notes — shift handover

Box was captured mid-cutover. The last two seal rounds landed in the
packed image, but the desk was left running against the surface working
sheet from before the cutover, and the material preference was parked on
the surface plane during the incident review.

The monitor has been green all week — it reads the image freshness, not
the sheets — so do not take `HEALTH_OK` as a sign the seating is right.

Ops calendar, for context:

- chassis swap on the midas rack is booked through epoch 40;
- the kronos kernel window closed at epoch 25;
- device 6 was pulled at epoch 20 after the enclosure alarm;
- device 1 flapped early in the cycle and was returned to service.

The state plane under `/var/lib/ceph/ops/state/` is scratch — the desk
rebuilds it on every pass, so anything parked there by hand will not
survive a re-run.
