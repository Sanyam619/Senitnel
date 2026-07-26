# Idea seed — Day-Ahead Clearing Contest

**Status:** Platform Idea Proposal accepted (Similarity / Category / Idea quality / Metadata).  
**Next step:** Step 2a (`validate_loop` / authoring spec GO) → Step 2b files.  
**Do not** jump straight to `tasks/` without a GO authoring spec.

---

## Canonical task identity

| Field | Value |
| --- | --- |
| Suggested task slug | `day-ahead-clearing-contest` |
| Title | Day-Ahead Clearing Contest |
| `task.toml` category | `games` |
| Idea-form category | Interactive / Simulation Tasks / Games |
| Difficulty | `hard` |
| Languages (planned) | `bash`, `java` or `python` (sealed judge), not a greppable solver tree |
| Reference pattern | `blindfold-capture-contest` / `weiqi-capture-contest` (puzzles + sealed judge + contest card) |

**Do not name it** `*-forensics`, `*-adjudication`, `*-arbiter`, or ship ELF/Cargo engine sources in the zip (SE classifier bait).

---

## Use THIS idea text (category-safe)

This is the wording that cleared **all four** idea checks. Prefer it over older ISO/`market_judge.jar`/`/app/rounds/` drafts (those scored Strong Accept quality but often classified `data_proc`).

**Idea Category:** Interactive / Simulation Tasks / Games

**Task Idea Summary:**
```
Play twelve sealed puzzle rounds of the Day-Ahead Clearing Contest under /app/puzzles/: for each round, decide which generators clear, at what system marginal price, and whether the published reserve constraint binds, under the house contest rules in /app/docs/contest_rules.md. The sealed table judge is /app/bin/judge.jar (leave it unchanged). A kiosk projector under /app/kiosk/ often shows a different clearing — the sealed judge is authoritative. Submit the official contest card at /output/market-clearing-card.json only by running /app/ops/run_clearing_card.sh, which must invoke the sealed judge on every claimed clearing; cards the judge rejects are invalid. Card schema: version (integer, 1); rounds (array of twelve objects each with round_id string, cleared (array of objects with unit_id string, mw number, offer_price number), smp (number), reserve_binds (boolean), status (string among "feasible_clear","infeasible","reserve_short"); for infeasible or reserve_short rounds, also include refutation (string naming the rulebook clause id that blocks the naive full-clear)). Status feasible_clear requires a judge-accepted clearing whose cleared set, mw, and smp match the judge; infeasible requires a judge-accepted proof that no feasible clearing exists; reserve_short requires judge acceptance that energy clears but reserve is short, with reserve_binds true. Puzzle sheets under /app/puzzles/ list offer curves and reserve demand. Running /app/ops/run_clearing_card.sh twice must produce byte-identical /output/market-clearing-card.json.
```

**Associated Skills:**
```
day-ahead market clearing; system marginal price; generator offer curves; reserve constraints; sealed table judging; feasible vs infeasible rounds; contest card filing; puzzle-round adjudication
```

**Task Tags:**
```
contest, puzzles, judge, reserve, clearing
```

### Schema pin (authoritative nesting)

Clarify in Step 2a / tests (idea text above already nests correctly):

```text
/output/market-clearing-card.json
  version: int == 1
  rounds: length 12
    [].round_id: string
    [].cleared: [{ unit_id: string, mw: number, offer_price: number }, ...]
    [].smp: number
    [].reserve_binds: bool
    [].status: "feasible_clear" | "infeasible" | "reserve_short"
    [].refutation: string   # REQUIRED iff status in {infeasible, reserve_short}
```

Do **not** put `smp` / `reserve_binds` / `status` inside `cleared[]` objects.

---

## Category classifier discipline (`games`)

**Lead with:** play / puzzle rounds / contest card / sealed table judge / kiosk decoy.  
**Avoid on solver-visible surfaces:** forensics, API manuals, arbiter, engine, optimize, LP, “parse offers”, “compute clearing from CSV”, ship/fleet profiles, ETL verbs.

| Path | Role |
| --- | --- |
| `/app/puzzles/` | Round boards (offer curves + reserve demand) |
| `/app/docs/contest_rules.md` | House rules + clause ids (outcomes, not fix recipe) |
| `/app/bin/judge.jar` | Sealed authority (Python/Java jar aura like weiqi; no probe source in image) |
| `/app/kiosk/` | False-green projector drafts (non-authoritative) |
| `/app/ops/run_clearing_card.sh` | Desk entrypoint; must call judge; idempotent |
| `/output/market-clearing-card.json` | Graded contest card |

Instruction must be **goal-first contest language**, not “process market data into JSON.”

---

## Hardness design (do not ship a free LP booklet)

Frontier agents will write an in-container clearer if every round is textbook merit-order. Mirror games lessons from weiqi/blindfold:

1. **Multi-status matrix** — mix `feasible_clear`, `infeasible`, `reserve_short` so one global optimizer policy fails distant rounds.
2. **Refutations on blocked rounds** — clause_id coverage the judge checks; required ⊆ submitted or exact set per tests (document which).
3. **Kiosk false-green** — projector posts naive full-clear / wrong SMP; card must follow sealed judge.
4. **No answer-key sheets** — strip `# clear` / `# infeasible` labels from puzzle files.
5. **Oracle derives via judge**, not a hardcoded PV table with unused “search” helpers (blindfold 2026-07-23 lesson).
6. **Instruction symptoms-only** at Step 2b — denser idea summary ≠ final `instruction.md`. Document graded statuses/outcomes; do not paste the clearing algorithm.

Target: platform ≥ MEDIUM; design for HARD. Cheap gates: static → collapse → oracle 1x → NOP.

---

## Draft discovery budget (≥3; expand in Step 2a)

1. **Reserve vs energy polarity** — when energy clears but reserve is short → `reserve_short` + `reserve_binds true`, not `infeasible`. Location: judge + `contest_rules.md` scenario prose. Hide: exact MW arithmetic recipe.
2. **Clause-id vocabulary** — which rulebook clause blocks naive full-clear on each blocked round. Location: docs clause list + puzzle sheets. Hide: mapping table in instruction.
3. **SMP tie-break / marginal unit** — which offer sets `smp` when multiple units clear. Location: judge behavior + audit samples in docs/history. Hide: closed-form formula dump if it collapses the booklet.
4. **Kiosk non-authority** — projector lines that look legal under pass-through offers but fail adversarial reserve. Location: `/app/kiosk/`. Hide: “ignore kiosk” banner.

---

## Draft topology (3 candidates; Step 2a picks one)

**A. Rules × boards × card emitter**  
- `contest_rules.md` clause semantics, puzzle offer/reserve numbers, `run_clearing_card.sh` judge wiring. No single file suffices.

**B. Judge-backed search oracle**  
- Oracle searches commitments; tests re-invoke judge; kiosk drafts diverge; card entrypoint rebuilds from agent card + judge.

**C. Split energy/reserve ledgers on boards**  
- Some rounds only fail reserve; some fail energy feasibility; refutation clause ids differ — wrong global “always drop highest offer” fails the matrix.

---

## Step 2a / 2b checklist (before claiming ready)

- [ ] Read `AGENTS.md`, `task-type-taxonomy.md` (`games`), `idea-validation.mdc`, `task-creation.mdc`, `00-authoring-critical.mdc`, `AUTHORING_RIGHTS_AND_WRONGS.md`
- [ ] Produce GO authoring spec + reviewer appendix + evidence JSON (`version: 2`)
- [ ] Sealed judge only; strip judge sources from runtime image if built in Docker
- [ ] ≥20 files under `environment/` (excl. Dockerfile)
- [ ] `environment/.dockerignore`; no `COPY` of hidden paths from context
- [ ] `allow_internet = false`; verifier deps in Dockerfile
- [ ] `run_static_checks.py` → `collapse_check.py` → oracle 1x → NOP
- [ ] No forbidden zip roots (`output_contract.toml`, scaffolding names, etc.)
- [ ] `./scripts/cleanup-task-docker.sh day-ahead-clearing-contest` after zip work

---

## Distinct from existing bank

Not a clone of: `blindfold-capture-contest`, `superko-rule-forensics` / weiqi, kriegspiel chess, `airport-deicing-fluid-accountability`, `rail-yard-consist-recovery`, `in-doubt-transaction-recovery`. Domain is day-ahead **contest clearing** with SMP + reserve statuses under a sealed judge.

---

## Prompt paste for the next chat (copy as-is)

```
Build Terminal-Bench task `day-ahead-clearing-contest` (category games).
Start at Step 2a from specs/day-ahead-clearing-contest-idea-seed.md.
Use the category-safe idea text in that seed (puzzles/, contest_rules.md, judge.jar).
Do not use market_judge.jar or /app/rounds/ naming.
Follow AGENTS.md + idea-validation.mdc + task-creation.mdc + AUTHORING_RIGHTS_AND_WRONGS.md.
Design a 12-round sealed-judge contest with feasible_clear / infeasible / reserve_short,
clause refutations, kiosk false-green, oracle via judge (no hardcoded PV table).
Do not claim PASS/READY without oracle 1x + NOP evidence.
```
