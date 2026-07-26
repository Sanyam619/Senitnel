# Seating contract

## Preferred group

Each managed map has a preferred target group. The preferred group is the
weight resolved by folding the `conf.d` drop-ins in ascending filename order,
last layer wins. An eligible AO path is only seated when its group equals the
map's folded preferred group. Editing only `multipath.conf` leaves the drop-in
fold — and any residual overlay left behind by an aborted cutover — in force.

## Selection

For every map on the durable roster that is not inside its hold window, the
active path is the eligible AO path (generation at or above the durable floor)
whose group is the folded preferred group, chosen by highest priority. Maps
inside a hold window are not seated; they are reported under `holds` with the
epoch until which the hold lasts.

## path_ok

`path_ok` is true only when the runtime bindings seat exactly the expected
active path for every non-held roster map and the desk is running on durable
preference materials. A surface preference lets the substrate be
rematerialized from decoy materials, which fails this check even if the status
helper prints ready.

## schema_tag

`schema_tag` must equal the durable authority tag, not the surface tag.
