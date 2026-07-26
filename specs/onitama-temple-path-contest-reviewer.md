### Decision
GO — Attempt 1. Onitama temple-path booklet under `games`: sealed table
judge, twelve Sensei-to-move rounds, win/trap/fort with card-rotation and
refutation coverage. No repair/debug framing.

### Metadata
- Task name: onitama-temple-path-contest
- Title: Onitama Temple Path
- Category: games
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [onitama, temple-path, card-rotation, tournament, table-judge, puzzle-book]
- Milestones: 0

### Discovery budget
- Discovery: Official move-card offsets for the sixteen named cards and the
  180° facing flip when the opponent receives a card from the sideboard.
  Planned location: `/app/docs/contest_rules.md` + sealed judge behavior /
  match logs (not a closed-form stamp table in the instruction).
  Why instruction must not reveal it: pasting every offset collapses the
  booklet to transcription; agents must recover facing from docs + judge.

- Discovery: After a move, the used card becomes the sideboard and the prior
  sideboard enters the mover's hand — sensei whisper ignores this swap.
  Planned location: `/app/docs/contest_rules.md`, decoy in
  `/app/tools/sensei_hint.sh`.
  Why instruction must not reveal it: naming the whisper bug turns the task
  into a one-line diagnosis; agents must learn rotation from house rules.

- Discovery: Trap threat = a Sensei first card that does not finish, but a
  second Sensei ply with Pupil sitting still does; each such card needs a
  Pupil reply that kills the immediate follow-up.
  Planned location: `/app/docs/score_card.md`.
  Why instruction must not reveal it: answer-key threat lists collapse traps;
  fair outcome prose lives in docs, not instruction.

### Anti-trivialization verdict
Checks 1–18 PASS for a sealed-judge puzzle booklet (not repair). Check 19
PASS (≥3 discoveries above). Check 20 PASS (symptoms-only instruction).
Check 21 PASS (three topologies below). Hard-only gate PASS: card rotation ×
force/coop × refutations is beyond in-distribution chess mate.

### Topology enumeration (3 candidate fix topologies)
1. Search-oracle desk: `board_hunt` classify + `desk_books` schema token +
   `card_out` writer — no single module emits a correct twelve-row card.
2. Agent in-container engine: rules recovery + adversarial search +
   refutation enumeration — legality alone without force/coop fails distant
   cells.
3. Judge-driven probe loop: validate candidate lines under sealed jar while
   independently labeling trap threats — jar alone never prints verdicts.

### Rubric axes
- Verifiable: Pass — deterministic JSON + sealed replay.
- Well-specified: Pass — docs carry house rules; instruction names outputs.
- Solvable: Pass — expert Onitama + search in hours.
- Difficult: Pass — rotation × coop/force matrix.
- Interesting: Pass — real contest adjudication skill.
- Outcome-verified: Pass — grade the card, not the approach.

### Instruction completeness test
Symptoms-only; field vocabulary named; rules deferred to `/app/docs/`.

### Collapse audit
Smallest plausible patch is not a config flip. Residual hardness is play
search under rotating cards. Kiosk/sensei are false-green bait, not the
frontier.
