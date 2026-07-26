### Decision
GO — Attempt 1. Hard `system-administration` Redis Sentinel HA seating desk on live `/etc/redis/` + durable `/var/lib/redis/ops/`. Prefer × failover-journal tip × quorum × replica-attach coupling with surface MASTER-OK bait and rematerialize of naive sentinel monitor lines.

### Metadata
- version: 2
- Task name: redis-sentinel-quorum-failover-seating
- Title: Redis Sentinel Quorum Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["tool_specific"]
- Tags: ["redis", "sentinel", "failover-journal", "quorum", "generation-gate", "ops-seating"]
- Milestones: 0

## Authoring Brief

### Public contract
Seat Redis HA so `/app/ops/run_sentinel_seat.sh` emits `/output/sentinel-seat.json` with `schema_tag` (`sentinel-seat-v1`), `masters` (array of `{name, addr, generation, authoritative}`), `replicas` (array of `{master, addr, lag, attached}`), and `seat_ok`. Live materials under `/etc/redis/` and `/etc/redis/sentinel.d/`; durable prefer + failover journal under `/var/lib/redis/ops/`. Surface `/usr/local/bin/redishhealth` may print MASTER-OK while deep seating is wrong. Frozen fixtures under `/app/data/redis/` must not be rewritten. Entrypoint twice → byte-identical; verifier re-seats after wiping `/output`.

### Triviality Ledger
- Independent always-wrong polarity stubs alone → REJECT; couple prefer rematerialize so naive monitor edits undo.
- Answer-shaped site-standard tip matrix / exact authoritative checklist in instruction → REJECT; outcomes in docs, EXPECTED in tests.
- Schema-only / existence-only tests → REJECT; every cell grades journal tip × floor × quorum × attach.
- Language-source rebuild frontier → REJECT; correct sealed `sentiseat`; broken opaque bash ops stages.
- Repair/debug / “fix Redis” framing → REJECT; seating/ops desk language only (sysadmin classifier).

### Per-gate Pitfall Inventory
- RC6: instruction stays symptoms-only; detailed rules under `/app/docs/seating_contract.md`.
- RC7: oracle rewrites ≥4 coupled helpers + durable prefer/receipt/site-standard (≥80 LOC).
- CR7: opaque helper names (`helm_r`, `axle_n`, `mesh_k`, `skim_p`, `sock_v`, `slate_j`); no instruction nouns on fix path.
- Sufficiency: document authoritative / attached / receipt / abort forensic outcomes in docs (not buried only in tests).
- Abort/receipt: matching `key=value` receipt skips rematerialize; live `90-local.conf` stays present with site-standard tokens.

### Initial Draft Commitments
- Prefer plane `surface` vs `durable` + matching `apply.ok` (`gen=` + `mode=seal`).
- Failover journal sealed tip at `gen.target`; older sealed / later provisional are history.
- Quorum under prefer-selected policy (surface minority decoy vs durable majority).
- Replica `attached=false` when replica still points at a superseded master addr.
- Generation floor: tip gen ≥ floor required for `authoritative=true`.
- `redishhealth` ignores journal epoch / quorum / attach.

### Discovery budget
1. Sealed failover tip selection (`kind=cutover` ∧ `gen==gen.target` ∧ `mode=seal`) — `/var/lib/redis/ops/failover_journal.jsonl`.
2. Prefer × receipt rematerialize of `/etc/redis/sentinel.d/` monitor lines from surface decoy vs durable tip addrs — `ops/helm_r.sh`.
3. Quorum sheet selection (surface minority vs durable majority) — `bag/skim_p.sh` + prefer.
4. Replica attach = replica master-addr equals durable tip addr (not live decoy) — `bag/sock_v.sh`.

### Topology distribution
1. Durable settle: `helm_r` + `axle_n` + `slate_j`/`sentiseat`.
2. Quorum × authoritative: `skim_p` + journal tip + floors.
3. Replica attach × superseded: `sock_v` + tip addrs + replica sheets.
4. Fold × abort forensic: `mesh_k` + live site-standard + abort package untouched.

### Flipping-point contract
| id | path | controls |
| -- | ---- | -------- |
| A | ops/helm_r.sh | prefer/receipt, rematerialize, re-entry |
| B | ops/axle_n.sh | tip gens/addrs, generation floors |
| C | bag/skim_p.sh | quorum under prefer, authoritative |
| D | bag/sock_v.sh | replica attach/lag matrix |
| E | rim/mesh_k.sh | fold/site-standard, abort polarity |
| F | deck/slate_j.sh + sentiseat | schema, seat_ok, idempotency |

### Symbol table (oracle touch)
- `ops/helm_r.sh` → `helm_r`
- `ops/axle_n.sh` → `axle_n`
- `rim/mesh_k.sh` → `mesh_k`
- `bag/skim_p.sh` → `skim_p`
- `bag/sock_v.sh` → `sock_v`
- `deck/slate_j.sh` → `slate_j` (delegates to `/app/bin/sentiseat`)
