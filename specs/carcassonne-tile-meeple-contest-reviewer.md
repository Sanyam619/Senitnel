# Reviewer appendix — carcassonne-tile-meeple-contest

## Discovery budget (solver must extract from docs/judge/runtime)

1. **Edge-match + rotation legality** — live in `/app/docs/contest_rules.md` +
   judge `legal`/`apply`; instruction only names house notes under `/app/docs/`.
2. **Contested-feature polarity** — dual-colour meeples on a completed feature
   score nothing for Red; discovered via judge apply/validate, not instruction.
3. **Farmer majority scoring** — farm regions score 3 per touched completed
   city only with sole Red majority; sensei ignores this (bait).
4. **Threat / refutation contract** — trap first placements that would finish
   next turn under Blue-pass need a Blue seat reply; coverage is ⊆ not equality.
5. **Three-turn Red budget + score floor** — floors and budget in house notes;
   kiosk uses a fourth cooperative turn as win bait.

## Topology distribution

1. **Classify × line × card write** — `op_b` search, `op_c` emit, `op_a`
   dialect gate; no single package greens the suite.
2. **Force vs coop vs fort** — wrong L2 on shared features fails distant
   win/trap/fort cells together.
3. **Farmer vs city/road** — sensei-green city completions still fail farm
   majority cells and score_delta replay.

## Residual hardness
Search under edge matching, contested seats, and farmer scoring; sealed judge
replays; kiosk/sensei false greens. Not independent polarity stubs.

## Category guard
`games` play booklet: `/app/puzzles/`, `/app/bin/judge.jar`, `/app/answers.json`,
tags lead `puzzle-book`/`tournament`/`table-contest`. No repair/cutover prose.
