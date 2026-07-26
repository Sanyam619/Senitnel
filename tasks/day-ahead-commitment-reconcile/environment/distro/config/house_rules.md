# House rules

## Commitment lines

Assigned MW must stay within each unit capacity. Energy-feasible lines meet demand exactly. Reserve is met when online leftover capacity is at least `reserve_mw`.

## System marginal price

On an energy-feasible line, `smp` is the highest offer among online units.

When several energy-and-reserve-feasible lines exist, report the lowest achievable `smp`. Ties break toward largest reserve headroom, then ascending unit_id order.

## Reserve binding

`reserve_binds` is true when headroom equals `reserve_mw` on the reported energy line. It is true on `reserve_short` rounds and false on `infeasible` rounds.

## Statuses

- `feasible_clear` — a line meets demand and reserve; report one under the SMP/headroom tie-break.
- `reserve_short` — demand is reachable but no energy line also meets reserve. Report an energy-feasible cleared line that fails reserve, `reserve_binds` true, and a clause id.
- `infeasible` — demand cannot be met. Empty `cleared`, `reserve_binds` false, and a clause id.

## Clause ids

- `C_CAP` — total capacity below demand.
- `C_RES` — demand reachable but reserve unreachable on every energy-feasible line.

Blocked rounds cite the clause that stops the naive full-capacity clear when that naive line is not a legal winning clear.
