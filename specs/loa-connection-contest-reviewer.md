### Decision
GO — Attempt 1. Same decision line as the authoring spec.

### Metadata
- Task name: loa-connection-contest
- Title: Lines of Action Connection Contest
- Category: games
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [lines-of-action, connection-contest, tournament, table-judge, puzzle-book]
- Milestones: 0

### Discovery budget
- Discovery: a checker steps exactly as many squares as there are checkers of either colour on the whole rank it walks along (sideways) or the whole file it walks along (up and down); it may hop its own checkers but not an enemy checker, and it may finish on an enemy square.
  Planned location: `/app/docs/contest_rules.md`, the judge's `probe` refusals, and the sample dialogues under `/app/history/`; sensei deliberately ignores both the count and the block.
  Why the instruction must not reveal it: naming the sensei defect turns the whole step law into a one-line checklist.

- Discovery: a side is gathered when its remaining checkers form one group under orthogonal *or* diagonal touching, and a lone checker counts as gathered.
  Planned location: `/app/docs/board_format.md` grouping section and the judge's component readouts.
  Why the instruction must not reveal it: Hex/Quoridor habits push agents to 4-adjacency, and two win endings are one group only on the diagonal.

- Discovery: a pressing move does not gather on its own but admits an immediate follow-up gather while the other side stands still; an answer is a legal reply that kills that follow-up. Coverage is required ⊆ submitted.
  Planned location: `/app/docs/tournament_card.md` and `/app/docs/component_floors.md`; the verifier recomputes the pressing set.
  Why the instruction must not reveal it: pasting the per-board pressing sets is an answer key.

### Anti-trivialization verdict
1 Disclosure-collapse: PASS — honest outcomes in docs still leave the search work.
2 Hidden-instance: PASS — twelve mixed rounds, not one broken file.
3 Single-artifact repair: PASS — no repair framing; the deliverable is a contest card.
4 Generalization: PASS — win/trap/fort matrix across twelve sheets.
5 Prompt-honesty: PASS — symptoms-only instruction.
6 Cheating-vs-difficulty: PASS — seal immutability is anti-cheat only.
7 Mechanical-fix: PASS — the domain work is the card.
8 Localized-fix: PASS — force × cooperative × answers × components.
9 Oracle-locality: PASS — search packages, not one replace.
10 Small declarative-cluster: PASS — every row needs search.
11 Grep-collapse: PASS — opaque oracle symbols and package names.
12 Pre-factored-helper: PASS — sensei and kiosk are decoys, not solvers.
13 Recipe-discount: PASS — Lines of Action step law is far from textbook BFS.
14 Security-aura: N/A games.
15 Orthogonal-checklist: PASS — force, cooperative, and answer work are coupled.
16 Harness-discount: PASS — the jar is sealed tooling, not a declared language.
17 One-pass solvability: PASS — sensei bait plus the count law plus diagonal grouping.
18 Hard-only gate: PASS — intended hard.
19 Discovery budget: PASS — three items above.
20 Instruction specificity: PASS — symptoms-only.
21 Topology distribution: PASS — three topologies below.

### Topology enumeration (3 candidate fix topologies)
1. Step law × force search × card emit — `moves_for` / `forcing_moves` / `build_round` must agree; a correct force search on illegal steps fails judge validation, and legal steps with no force search misfile traps as wins.
2. Pressing coverage × answers × component floors — `build_trap_refs`, `answer_to`, and `scored_components` must coordinate; any one alone leaves other cells red.
3. Cooperative reach × diagonal grouping × seal immutability — the fort/trap split needs the unopposed budget and 8-adjacency; editing seals fails immutability.

### Rubric axes
1 Verifiable: Pass — deterministic pytest plus the sealed judge.
2 Well-specified: Pass — docs define the step law, statuses, and fields.
3 Solvable: Pass — an expert with search can finish in hours.
4 Difficult: Pass — count-law legality, adversarial answers, diagonal grouping.
5 Interesting: Pass — real adjudication skill on an uncommon board game.
6 Outcome-verified: Pass — the card is graded, not the process.

### Hardness axes
1 Discover: Pass — house rules plus the sensei mismatch.
2 Synthesize: Pass — step legality × force budget × grouping.
3 Diagnose: Pass — symptoms only (the overnight draft is wrong), no causes.
4 Navigate coupling: Pass — a wrong grouping or step reading flips many rows.
5 Reason beyond training: Pass — Lines of Action with a house step law is off-distribution.

### Instruction completeness test
The instruction states the contest goal and the artifact; every graded rule lives under `/app/docs/`. The task cannot be solved from the instruction alone.

### Collapse audit
The smallest plausible submission is not a copy of the overnight draft or a sensei transcription — both misfile every trap and fort. The editable frontier spans move legality, force search, cooperative reach, answer coverage, and component floors, and residual hardness is Lines of Action reasoning against surface bait.
