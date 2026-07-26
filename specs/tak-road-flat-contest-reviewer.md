### Decision
GO — Attempt 1. Same decision line as the authoring spec.

### Metadata
- Task name: tak-road-flat-contest
- Title: Tak Road Contest
- Category: games
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [tak, road-contest, tournament, table-judge, puzzle-book, score-card]
- Milestones: 0

### Discovery budget
- Discovery: Carry limit equals board size; slides that take more pieces than the limit are illegal even when they would complete a visual road.
  Planned location: `/app/docs/contest_rules.md` + judge `validate` rejection; sensei deliberately ignores the limit.
  Why instruction must not reveal it: naming the sensei bug collapses the carry-limit trap into a one-line checklist.

- Discovery: Standing stones never count as road stones; only flats and capstones of the road color do. Capstone may flatten a standing top by sliding alone onto it.
  Planned location: `/app/docs/contest_rules.md` + board_format piece alphabet; puzzles include standing blockers.
  Why instruction must not reveal it: Hex/Quoridor agents otherwise treat every friendly top as a link cell.

- Discovery: Trap threats are first moves that do not finish a road but admit a second White finish if Black passes; required ⊆ submitted refutations.
  Planned location: `/app/docs/tournament_card.md` threat section; verifier recomputes threat set.
  Why instruction must not reveal it: pasting the per-board threat set is an answer key.

### Anti-trivialization verdict
1 Disclosure-collapse: PASS — honest outcomes in docs still leave search work.
2 Hidden-instance: PASS — eleven mixed boards, not one broken file.
3 Single-artifact repair: PASS — no repair framing; card filing.
4 Generalization: PASS — matrix of win/trap/fort.
5 Prompt-honesty: PASS — symptoms-only instruction.
6 Cheating-vs-difficulty: PASS — seal immutability is anti-cheat only.
7 Mechanical-fix: PASS — domain work is the card.
8 Localized-fix: PASS — force × coop × refs × length.
9 Oracle-locality: PASS — search packages, not one replace.
10 Small declarative-cluster: PASS — positions require search.
11 Grep-collapse: PASS — opaque oracle symbols.
12 Pre-factored-helper: PASS — sensei/kiosk are decoys.
13 Recipe-discount: PASS — Tak midgame not textbook Hex BFS alone.
14 Security-aura: N/A games.
15 Orthogonal-checklist: PASS — coupled force/coop/threat.
16 Harness-discount: PASS — jar is sealed tooling.
17 One-pass solvability: PASS — sensei bait + carry + standing.
18 Hard-only gate: PASS — intended hard.
19 Discovery budget: PASS — three items above.
20 Instruction specificity: PASS — symptoms-only.
21 Topology distribution: PASS — three topologies below.

### Topology enumeration (3 candidate fix topologies)
1. Force-search × classify × card emit — `force_win` / `classify` / `build_round` must agree; force alone without refs fails traps; classify alone without sequences fails wins.
2. Threat coverage × judge validate × road_len — trap refs, legal replies, and exact lengths must coordinate; any one alone leaves other cells red.
3. Carry-legal slides × standing-aware roads × seal immutability — illegal carry or standing-as-road greens sensei but fails judge; editing seals fails immutability.

### Rubric axes
1 Verifiable: Pass — deterministic pytest + sealed judge.
2 Well-specified: Pass — docs define statuses and fields.
3 Solvable: Pass — expert Tak/search in hours.
4 Difficult: Pass — stack rules + adversarial traps.
5 Interesting: Pass — real tournament adjudication skill.
6 Outcome-verified: Pass — grade the card, not the process.

### Hardness axes
1 Discover: Pass — house rules + sensei mismatch.
2 Synthesize: Pass — stacks × roads × threats.
3 Diagnose: Pass — symptoms (draft wrong), not causes.
4 Navigate coupling: Pass — wrong L2 flips many cells.
5 Reason beyond training: Pass — Tak less common than Hex/Quoridor.

### Instruction completeness test
Symptoms-only contest goal; detailed vocabulary under `/app/docs/`. Cannot solve from instruction alone.

### Collapse audit
Smallest plausible patch is not a sed of one file; editable frontier spans search + card assembly; residual hardness is Tak domain reasoning against surface bait.
