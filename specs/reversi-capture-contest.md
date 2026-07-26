### Decision
GO — Attempt 1. Games contest booklet (no repair/debug): sealed `/app/bin/judge.jar`, eleven Black-to-move midgame Reversi rounds, corner-safe ≠ max-mobility ranking, coop_sweep traps that false-green under disc-greedy/sensei, refutation coverage on traps, deterministic kiosk emit. Hardness in multi-round contest adjudication, not source patches.

### Metadata
- version: 2
- Task name: reversi-corner-mobility-contest
- Title: Reversi Corner-Mobility Contest
- Category: games
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["reversi", "mobility-contest", "tournament", "score-card", "table-judge", "puzzle-book"]
- Milestones: 0

## Authoring Brief

### Public contract

A Reversi corner-mobility tournament under a sealed table judge. Agents classify eleven midgame rounds and file a contest score card. Primary work is Othello/Reversi contest reasoning (corner safety, mobility delta, cooperative sweep traps, refutation coverage) — not repairing printer or judge sources.

**Symptoms / framing (instruction.md level):**
- Eleven Black-to-move rounds under `/app/puzzles/`.
- Rulebook, announce customs, and mobility floors under `/app/docs/`.
- Sealed judge at `/app/bin/judge.jar`; sensei under `/app/tools/` is non-authoritative; kiosk drafts may disagree.
- Submit `/output/reversi-card.json`. Filing helper `/app/kiosk/emit_card.sh` run twice must produce byte-identical output.
- Do not alter the sealed judge or puzzle sheets.

**Required outcomes (card schema):**
- `schema_tag` (string) matches house card tag in docs.
- `rounds` array length 11; each row: `board_id` (string), `status` (string), `best_move` (string), `mobility_delta` (integer), `corner_safe` (boolean), `refutations` (array of `{move, reply}`), `coop_sweep` (boolean).
- Status vocabulary (`win` / `trap` / `fort`) and ranking rules live in `/app/docs/` (not as an instruction checklist).
- Trap/unwinnable-with-coop rounds require refutation coverage for every graded losing first move under the house threat rule.
- Corner-safe best moves are not always max-flip or max-mobility greps; traps green under naive disc-count / sensei.

**Constraints:**
- `category = games`; `allow_internet = false`; `languages = ["bash"]` (jar is sealed tooling).
- No repair/debug framing; not multi-container / not UI.
- Tournament nouns only (`puzzles/`, `judge.jar`, `score-card`, `table-judge`) — no forensics/API/predicate aura.

### Failure topology

Three clusters. (1) Corner-safe ranking vs greedy disc/mobility: filing max-flip or max-raw-mobility as `best_move` on win rounds fails exact-move and corner_safe cells. (2) Coop sweep traps: sensei/kiosk greening `coop_sweep` while `status` must stay `trap` with refutations. (3) Fort polarity: rounds that never sweep even under cooperative White must be `fort` with `coop_sweep` false and empty refutations — labeling them traps fails coverage and fort tests.

Hard because wrong L2 (trap vs win vs fort) fails several rounds; mobility floors couple to best_move; refutation ⊆ threat set must cover every graded losing first move.

### Environment shape

- Sealed judge.jar (bytecode-only zipapp/jar; sources compiled in Docker then stripped).
- Eleven puzzle boards, contest docs (rulebook, card schema, mobility floors, announce customs, board format), match-log samples for announce dialect, kiosk emit + disc-count drafts, sensei_hint.sh false-green on traps.
- No golden card under environment/.

### Required artifacts

- Standard layout: instruction.md, task.toml, output_contract.toml, environment/**, solution/solve.sh (+ derive helpers), tests/test.sh + test_outputs.py.
- ≥20 non-Docker environment files.
- Oracle derives card via Reversi search + judge validate (≥30 substantive LOC); no hardcoded full answer blob as the only path.

### Test plan

- Schema + schema_tag + eleven rounds + required fields.
- Judge integrity vs `/opt/tbench/` seal copy; puzzles immutable.
- Win rounds: exact best_move, corner_safe true, mobility_delta matches independent ranking, floors met.
- Trap rounds: status trap, coop_sweep true, refutation coverage (required ⊆ submitted), White replies keep corner pressure.
- Fort rounds: status fort, coop_sweep false, empty refutations.
- Sensei/kiosk false-green: disc-greedy drafts disagree with sealed statuses on traps.
- emit_card.sh double-run byte-identical `/output/reversi-card.json`.
- Deep cells: best_move ≠ max-flip on at least one win; mobility_delta not equal to flip count.

Opaque mineral test names. EXPECTED only in tests. Multiple search strategies OK if outcomes match house rules + judge.

### Drafting guardrails

Symptoms-only contest instruction. No per-round answer key, no fix checklist, no “patch the kiosk”. Opaque oracle package names. Docs describe outcomes and vocabulary without listing per-board answers. Prefer jar judge (no ELF).

### Triviality Ledger

- Copying kiosk/sensei disc-greedy lines as wins fails trap and corner_safe tests.
- Max-mobility without corner filter fails win best_move cells.
- Labeling all coop_sweep rounds as win fails traps that need refutations.
- Omitting refutations on traps fails coverage.
- Fort rounds mislabeled trap fail coop_sweep false asserts.
- Hand-written JSON that ignores judge-legal moves fails legality/mobility probes.

### Per-gate Pitfall Inventory

- RC1: Oracle derives via search; never restore a golden card from environment/.
- RC3: Tests assert domain outcomes (moves, deltas, statuses, refutations), not mere JSON existence.
- RC5: No golden reversi-card.json under environment/.
- RC6: Instruction symptoms-only; floors/threat rule recovered from docs + judge.
- RC7: derive path ≥30 substantive LOC.
- Category: contest paths + jar; languages=bash; avoid SE tooling aura.
- Static: allow_internet=false, .dockerignore, absolute paths, hashed pytest lockfile, PLW1510/PLR0124 clean.

### Initial Draft Commitments

- `tasks/reversi-corner-mobility-contest/` full standard tree
- `environment/judge_src/` build-only
- `environment/puzzles/board_01.txt` … `board_11.txt`
- `environment/docs/{contest_rules,score_card,board_format,mobility_floors,announce_customs}.md`
- `environment/kiosk/emit_card.sh` + draft helpers
- `environment/tools/sensei_hint.sh`
- `environment/history/` announce samples

### Discovery budget (≥3)

1. **Corner-safe definition vs X-square / immediate White corner reply** — lives in `contest_rules.md` + judge `apply` fields; instruction must not paste the predicate checklist beside greppable boards.
2. **Mobility_delta formula and win floor / lex tie-break for best_move** — lives in `mobility_floors.md` + score_card; must not appear as answer-key numbers in instruction.
3. **Trap threat set (which losing first moves need refutations) vs sensei fillability** — lives in contest_rules threat section; sensei deliberately greener; instruction only says sensei is non-authoritative.
4. **Announce dialect for judge line checks (`flips:N` / `+corner`)** — lives in history logs + announce_customs.md.
5. **schema_tag exact string** — lives in score_card.md only.

### Topology distribution (≥3)

1. **Win ranking cluster** — engine legal-gen + corner_safe filter + mobility_delta + floor/tiebreak across docs and search (≥3 loci: rules, floors doc, derive ranker).
2. **Trap/refutation cluster** — coop_sweep simulator + threat enumeration + White corner/fighting reply (≥3 loci: coop policy, threat rule, refutation emit).
3. **Fort + emit determinism cluster** — fort classification + card schema emit + double-run canonicalize (≥3 loci: sweep horizon, score_card schema_tag, emit_card.sh).
