### Decision
GO — Attempt 1. Same as authoring spec.

### Metadata
- Task name: connect-four-zugzwang-contest
- Title: Connect Four Zugzwang
- Category: games
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [connect-four, zugzwang, threat-parity, tournament, table-judge, puzzle-book]
- Milestones: 0

### Discovery budget
- Discovery: Five Yellow drops is the house force/coop budget; a seventh-drop
  cooperative hunt is kiosk bait only.
  Planned location: `/app/docs/contest_rules.md`, kiosk `draft.py`
  Why instruction must not reveal it: naming the bait budget collapses trap/draw
  discrimination into "ignore the printer."

- Discovery: Trap threats are first Yellow columns that do not connect now but
  would on the next Yellow drop if Red sits still; each needs a Red reply that
  kills that immediate follow-up.
  Planned location: `/app/docs/contest_rules.md` + sealed judge apply/validate
  Why instruction must not reveal it: pasting the threat predicate next to empty
  stubs collapses to transcription (weiqi/amazons lesson).

- Discovery: Draw rounds still grade losing first drops — Yellow columns that
  let Red connect on the next Red drop — with refutation coverage, even when
  `coop_win` is false.
  Planned location: docs + verifier engine
  Why instruction must not reveal it: without discovery, agents leave draw
  refutations empty after classifying "no coop four."

### Anti-trivialization verdict
Checks 1–21 pass for a sealed-judge games booklet: multi-board matrix, kiosk
false-green, sensei legality bait, parity×zugzwang reasoning beyond naive
connect search, no repair/debug framing.

### Topology enumeration (3 candidate fix topologies)
1. Search oracle over sheets: desk schema token + per-sheet classifier + card
   writer — no single module produces a full correct card.
2. Agent writes an in-container engine and probes the sealed jar — still must
   cover force vs coop vs draw and refutation ⊆ across twelve sheets.
3. Hybrid jar-validate + hand lines — force preservation and draw refutations
   still fail if parity/threat rules are wrong.

### Rubric axes
- Verifiable: Pass — sealed judge + recomputed engine.
- Well-specified: Pass — docs carry house rules; instruction symptoms-only.
- Solvable: Pass — expert C4 search in hours.
- Difficult: Pass — parity×zugzwang×refutations; naive four-hunt fails.
- Interesting: Pass — tournament booklet / C4 theory.
- Outcome-verified: Pass — card + jar replay, not process.
