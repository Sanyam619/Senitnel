# Authoring Brief — glusterfs-volume-quorum-seating

## Decision

**GO** — hard system-administration seating desk. Primary activity is operating
live `/etc/glusterfs/` and durable `/var/lib/glusterd/` until the desk settles
and `/app/ops/run_gluster_seat.sh` emits a correct `/output/gluster-seat.json`.

## Category

`system-administration` (open). Live distributed-volume seating via ops —
matches taxonomy authoring guidance (live `/etc`/`/var`, false-green surface
health, rematerialize authority). Not SE: no language-source rebuild frontier;
`languages = ["bash"]`.

## Languages

`bash` (ops helpers + seating entrypoint). Correct sealed publisher
`/app/bin/glusterseat` (bash/python wrapper). Surface bait
`/usr/local/bin/glusterhealth`.

## Symptoms-only instruction (draft)

Live Gluster volume seating under `/etc/glusterfs/` and `/var/lib/glusterd/`
was captured mid-window and drifted from the durable brick authority.
`/usr/local/bin/glusterhealth` may print started while deep seating is wrong,
and sheet edits made without settling the desk are gone again on the next
pass.

Bring the desk to a correct, durable end-state and produce
`/output/gluster-seat.json` by running `/app/ops/run_gluster_seat.sh`. It
carries `schema_tag` `gluster-seat-v1`, one `volumes` row per roster volume
(with bricks, quorum, generation, started), the heal pending rows in `heals`,
and `seat_ok`. Acceptance rules — brick-set agreement against the durable
journal, generation floors, quorum under the prefer-selected policy, held
bricks excluded from the started set, heal pending counts, the drop-in policy
fold, and the receipt the state plane must carry — live under `/app/docs/`.
Frozen fixtures under `/app/data/gluster/` are integrity-pinned. Grading clears
`/output` and re-runs the desk twice; the two reports must be byte-identical.
Hand-authored JSON fails.

Ledger vocabulary: schema_tag, volumes, name, bricks, quorum, generation,
started, heals, volume, pending, seat_ok.

## Discovery budget (≥3)

1. **Sealed journal tip selection** — authoritative cutover row is
   `kind=cutover` ∧ `gen==gen.target` ∧ `mode=seal`; later provisional /
   earlier sealed windows are history. Lives in
   `/var/lib/glusterd/ops/brick_journal.jsonl`. Instruction must not name the
   filter predicates.
2. **Prefer × receipt rematerialize** — surface plane refreshes live brick
   sheets from `surface.bricks` (including revoked bricks) and re-copies the
   abort package; durable plane requires matching `apply.ok` (`gen=` +
   `mode=seal`) and refreshes from the sealed journal brick sets. Lives in
   `ops/reef_t.sh` + `prefer.toml`. Instruction states the outcome, not the
   gate algebra.
3. **Held-brick × quorum × heal coupling** — an open hold on any durable brick
   blocks `started` for that volume and increments `heals[].pending`; surface
   health ignores holds. Lives in `bag/flint_k.sh`, `bag/peat_x.sh`, and
   `glusterseat`. Instruction must not list which volume/brick is held.

## Topology distribution (≥3 topologies, ≥3 loci each)

1. **Durable cutover settle:** `reef_t` (plane+receipt) + `barn_w` (sealed tip
   gens/bricks/quorum) + `slate_j`/`glusterseat` (agreement). No single locus
   greens seat_ok.
2. **Hold/heal matrix:** `flint_k` (open holds) + `peat_x` (pending counts) +
   `glusterseat` (started excludes held bricks). Fixing only holds without
   heal still fails heal cells; heal without hold still starts wrongly.
3. **Policy fold × abort forensic:** `clay_m` (last-wins fold) + live
   `90-local.conf` site-standard tokens + abort package left forensic. Fold
   alone with abort still rematerialized fails abort/receipt tests.

## Flipping-point contract

| id | path | controls (subset) |
| -- | ---- | ----------------- |
| A | rim/clay_m.sh | fold/site-standard, abort polarity, seat_ok |
| B | ops/barn_w.sh | generation floors, brick tips, started matrix |
| C | bag/flint_k.sh | hold blocks, heal pending, started matrix |
| D | ops/reef_t.sh | prefer/receipt, rematerialize, re-entry |
| E | deck/slate_j.sh + glusterseat | schema, heals, seat_ok, idempotency |

No single location flips a majority of tests.

## Symbol table (oracle touch)

- `ops/reef_t.sh` → `reef_t`
- `ops/barn_w.sh` → `barn_w`
- `rim/clay_m.sh` → `clay_m`
- `bag/flint_k.sh` → `flint_k`
- `bag/peat_x.sh` → `peat_x`
- `deck/slate_j.sh` → `slate_j` (delegates to `/app/bin/glusterseat`)

## Hardness notes

- Do not ship independent always-wrong polarity stubs as the whole frontier.
- Couple prefer rematerialize so naive brick-sheet edits undo.
- Document outcomes in `/app/docs/seating_contract.md` (fairness), keep
  instruction symptoms-only.
- Correct sealed publisher; broken stages are opaque bash helpers.
- Distinct from Ceph CRUSH / LVM cache / dm-thin by brick-set equality,
  prefer-selected quorum, and per-brick hold → heal pending.

## Reviewer Appendix

See platform seating postmortems (autofs / lvm / backup-restore): keep live
drop-in present with site-standard tokens; receipt is `key=value`; do not
treat QC ACCEPT as hardness evidence.
