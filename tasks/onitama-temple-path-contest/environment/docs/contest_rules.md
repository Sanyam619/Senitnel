# Contest rules

Sensei moves first on every sheet. A finish is either **temple** (Sensei's
master steps onto the Pupil temple at `c5`) or **master capture** (any Sensei
piece lands on the Pupil master). Pupil wins the same ways mirrored (`c1`
temple, Sensei master captured) — fighting replies may do that.

## Cards and rotation

Each side holds two move cards; one card sits on the sideboard. On a turn the
mover chooses one hand card, moves one of their pieces by an offset on that
card, then:

1. the used card becomes the new sideboard, and
2. the previous sideboard enters the mover's hand.

Offsets are printed stamp-relative. When Pupil uses a card, both axes flip
(180°). Landing on your own piece is illegal; landing on an enemy piece captures
it. Pieces never jump blockers — Onitama moves are point-to-point.

The sixteen named cards and their stamp offsets live with the sealed judge; the
match logs show the colour-tagged dialect in play.

## Mate budget

Each sheet prints `mate_budget`: the maximum number of Sensei plies allowed for
a finish under that round's reading.

## Verdicts

- **win** — Sensei can force a finish within `mate_budget` against every legal
  Pupil reply (cards rotating for both sides).
- **trap** — Pupil can hold the fight off under adversarial play, but Sensei
  still finishes within `mate_budget` once Pupil sits still (no Pupil piece
  moves; Sensei cards keep rotating with the sideboard).
- **fort** — even with Pupil sitting still, no Sensei finish fits inside
  `mate_budget`.

`coop_temple` is true exactly when that friendly finish exists (win and trap),
and false on fort.
