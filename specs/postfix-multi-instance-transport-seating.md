# Authoring Brief — postfix-multi-instance-transport-seating

## Category

`system-administration` — live MTA multi-instance seating on `/etc` + `/var`, not writing a mail server.

## Goal

Seat the Postfix multi-instance desk so `/app/ops/run_postfix_seat.sh` emits
`/output/postfix-seat.json` with durable instance tips, prefer nexthop map fold,
abort-fragment honor polarity, and `seat_ok`.

## Languages

`bash` (ops helpers; Python only for deterministic fold/emit, same as sibling seating desks).

## Hardness (coupled loci)

1. Durable prefer tip × gen.target (sealed+complete beats incomplete later batch)
2. Instance `queue_dir` + generation ≥ durable floor × journal admit/revoke
3. Prefer nexthop map in live main.cf (not live/surface decoy map)
4. Transport patterns colliding with a later abort fragment → `honored=false`
5. Abort rematerialize into master.d unless matching `cutover.ok` (`gen`+`mode=seal`)
6. Surface rematerialize undoes naive tip/map edits until prefer is durable/authority AND tip_bind matches gen.target
7. `postfixhealth` prints mail-ready without durable seat

## Residual broken (oracle rewrites)

`helm_r` (abort always), `axle_n` (wrong tip/floors), `sock_v` (all-active / decoy queues), `knit_q` (always surface).

## Shipped correct

`mesh_k` (transport fold + honor), `skim_p` (instance journal), `emit_m` (ledger).

## Symbol table

| path | symbol | purpose |
|------|--------|---------|
| ops/helm_r.sh | helm_r | receipt-gated abort → master.d |
| ops/axle_n.sh | axle_n | sealed prefer tip, site-standard, cutover receipt |
| rim/mesh_k.sh | mesh_k | transport fold + abort honor set |
| bag/skim_p.sh | skim_p | instance journal admit − revoke |
| wire/sock_v.sh | sock_v | apply queue_dir + active set to live instances |
| wire/knit_q.sh | knit_q | prefer×bind-gated surface rematerialize |
| deck/emit_m.sh | emit_m | emit postfix-seat.json |

## Instruction stance

Symptoms + outcomes only. No repair/debug framing. Point at `/app/docs/` for normative seating rules.
