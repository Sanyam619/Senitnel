# iouring-registered-buffer-lease-cutover — EASY collapse after fairness patch (2026-07-20)

Artifact: `difficulty_check_artifact (22).zip`

## Platform result

- Difficulty: EASY (need ≥ MEDIUM)
- Agents: Opus 80% (4/5), GPT-5.5 80% (4/5)
- Oracle 100%, NOP 0%
- After host-marker sufficiency fix (artifact 21), agents cleared almost everything

## Why it was easy

Primary work collapsed to a short ops checklist once host cleanup was
documented: set durable epoch from fleet, fold PrivateMounts, register,
seat, emit. Partial misses were single knobs (epoch 3 vs 7, one unit
fragment). Instruction-sufficiency analysis then wrongly pushed for naming
`fleet.toml` and `PrivateMounts=no` — that would make the task TRIVIAL.

## Redesign shipped

1. Compound seal tip `seal:{epoch}:{slot_prefix}` (harbor uses `legacy`)
2. Second drop-in `20-nest.conf` — fold must clear every live.d fragment
3. Preflight rewrites if seal incomplete, PrivateMounts still yes, host
   markers remain, or gen mismatch (rematerializes host + harbor epoch)
4. jobpulse dirty under the same incomplete cutover conditions
5. Broken `SieveB` writes harbor onto durable + incomplete seal (hand-edits
   alone fail when `leasectl` re-enters)
6. Tests re-enter `leasectl` / `bufreg` / `ledgerout --fold` / `nsbind` /
   preflight / jobpulse / emit — not artifact-only scoring
7. Fair outcomes in instruction without checklist recipes
   (`PrivateMounts=no` / `fleet.toml epoch=7`)
