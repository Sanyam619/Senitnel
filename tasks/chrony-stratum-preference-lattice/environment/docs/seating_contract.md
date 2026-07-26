# Seating contract

## Preference

`preference` in the seating report must reflect the active mode from
`/var/lib/time/ops/prefer.toml`. Graded seating requires `durable` or
`authority`. Modes `live` and `surface` keep the desk on surface materials.

## Selection

A peer is selected only when all of the following hold:

1. It appears on the durable roster.
2. Its stratum is inside the published band.
3. It is not listed in the hold window.

Held roster peers still appear in `sources` with `hold` true and `selected`
false. Off-roster live peers may appear with both flags false.

## sync_ok and offset

`sync_ok` is true only when the live chrony sources tree seats exactly the
selected peer set and the folded timesync NTP matches the durable primary NTP
from authority materials. Surface health tools may still print synchronized.

`offset_bound_ms` is the durable budget for the selected peer (when exactly one
peer is selected). It is not taken from surface health output.

## schema_tag

`schema_tag` must equal the durable authority tag, not the surface tag.
