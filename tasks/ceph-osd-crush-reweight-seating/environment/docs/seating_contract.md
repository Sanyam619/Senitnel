# Seating contract

What a correct desk end-state looks like. These are acceptance outcomes,
not a procedure.

## Report shape

`/output/crush-seat.json` is a JSON object with exactly these keys:

- `schema_tag` — the string `crush-seat-v1`.
- `osds` — array of `{id:int, host:string, weight:number, in:bool,
  up:bool, generation:int}`.
- `pools` — array of `{name:string, size:int, pg_num:int, degraded:bool}`.
- `seat_ok` — boolean.

The file ends with a trailing newline. Two consecutive seating passes must
leave byte-identical reports; the desk may not embed anything that varies
between passes.

## Durable authority

The packed image under `/var/lib/ceph/ops/` is the placement authority.
Its row text is mirrored at `/app/data/crush/crush_map.txt`; rows are
chronological. A device's standing row is the newest-generation row for
that device. The surface working sheet is not authority.

## Device standing

- `weight` reports the live sheet value divided by 1000.
- `up` is true only when the live sheet's milli value equals the standing
  row's milli value AND the standing row's generation clears the floor in
  `gen.low`. The floor is inclusive: a standing row at exactly the floor
  generation clears it.
- `in` is true only when the device is `up` AND the sealed record stream
  does not leave it out: order the device's rows by epoch; if the last
  action is `out`, the device is out. An `out` followed by a later `in`
  is in. A device absent from the record stream follows `up`.
- A device that is out by the record stream can still be `up` when its
  sheet and standing row agree.
- `generation` reports the standing row's generation, per device.

## Maintenance windows

A window row is active only while its `until_epoch` is strictly greater
than the desk clock in `now.mark`. An expired row has no effect. An
active window excludes its host from placement counting below, but the
devices on that host still report `in`/`up` on their own standing.

## Group degradation

`size` and `pg_num` come from the live group sheets. `degraded` is
computed, never copied: a group is `degraded=false` only when the number
of distinct hosts carrying at least one in+up device — excluding hosts
under an active window — is at least the group's `size`. The `state`
annotation in the group sheets is a monitor note from an earlier shift,
not the answer.

## Acceptance

`seat_ok` is true only when all of the following hold:

- every live reweight sheet equals its device's standing row;
- `prefer.toml` selects the durable plane;
- `state/apply.ok` exists as `key=value` lines carrying `gen=` equal to
  the value in `gen.aim` and `mode=seal`;
- `state/gen.live` equals `gen.aim`.

A group that is truthfully degraded does not by itself make `seat_ok`
false.

## Integrity

Everything under `/app/data/` must stay byte-identical to
`/app/packaging/fixtures.sha256`. The sealed copies `record.jsonl` and
`window.jsonl` must continue to match their `/app/data/ceph/` sources.
`HEALTH_OK` from `cephhealth` is not acceptance. Grading clears
`/output` and re-runs the desk; a hand-written report does not survive.
