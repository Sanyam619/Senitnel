### Decision
GO — Attempt 1. Same line as authoring spec.

### Metadata
- Task name: amazons-territory-enclosure-contest
- Title: Amazons Territory Enclosure
- Category: games
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [amazons, territory-contest, tournament, table-judge, puzzle-book, score-card]
- Milestones: 0

### Discovery budget
- Discovery: Exclusive reachable territory (not raw empty count) and floor 2
  Planned location: `/app/docs/contest_rules.md` + judge `territory` output
  Why instruction must not reveal it: sensei empty-count bait collapses otherwise
- Discovery: Trap threats are one-ply enclosure threats needing Black replies
  Planned location: contest_rules + score_card; tests recompute threats
  Why not in instruction: listing threats is the answer key
- Discovery: Kiosk allows a fourth cooperative turn and stamps every round win
  Planned location: `/app/kiosk/draft.py` behavior vs three-turn table budget
  Why not in instruction: naming the fourth-turn bug is a fix recipe

### Anti-trivialization verdict
Checks 1–21 pass for a games booklet: analysis task, not repair; multi-board
matrix; sealed judge; coupled force/coop/refutation; Amazons domain beyond
disc/liberty heuristics.

### Topology enumeration
1. Search oracle over sheets (engine + op_b + op_c) — no single module enough.
2. Agent writes card via judge probing without oracle packages.
3. Agent repairs kiosk emit to stable-correct card (emit alone insufficient).

### Rubric axes
Verifiable Pass; Well-specified Pass; Solvable Pass; Difficult Pass; Interesting
Pass; Outcome-verified Pass.

### Hardness axes
Discover/Synthesize/Diagnose/Navigate coupling/Reason beyond training: all Pass
via Amazons enclosure search vs surface bait.

### Instruction completeness test
Cannot solve from instruction alone — need docs + judge probing + multi-board
classification.

## Reviewer Appendix

### Implementation plan
Eleven 5x5 Amazons endgames sheets; sealed Java 17 judge; oracle search emits
`/output/amazons-card.json`; tests recompute verdicts and replay sequences.

### Oracle notes
`derive.sh` copies desk packages, double-emits card, validates sequences via jar.

### Collapse audit
Stage: implementation-plan
Smallest plausible successful patch: search-derived eleven-row card.
Residual hardness: move+arrow branching × exclusive territory × force vs coop.
Collapse verdict: PASS (WARN on booklet-class GX signals justified like hex/reversi).

### Naming-pass record
Instruction nouns include territory, enclosure, amazons, arrow, rounds, card.
Oracle symbols op_a/op_b/op_c/engine avoid those as function names.
Test names use mineral tokens (onyx, slate, beryl, …).
