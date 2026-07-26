# Contest rules

This booklet is a road contest on a Tak board. White tries to complete a
north–south road. Black answers with flat placements when the card asks for
fighting play.

## Road stones

Only flats and the capstone of a colour count toward that colour's road.
Standing stones never count as road stones, even when they belong to the
road-building side. Orthogonal adjacency only — no diagonals.

## Standing stones and flattening

A standing stone blocks stacking in the ordinary way. The sole exception in
this booklet: a **lone capstone** may slide onto a standing top and flatten
it. Flattening turns that standing stone into a flat of the same colour, with
the capstone ending on top. Multi-stone carries cannot flatten.

## Carry limit

When sliding a stack, White may take at most **5** pieces from the top of a
stack (the board size). Taking more is illegal even if the resulting layout
would look like a road on paper. Sensei whispers that ignore this limit are
not authoritative.

## Reserves

Each round ships `flats_w` / `flats_b` / `caps_w` / `caps_b`. Placements spend
from those reserves. Slides do not spend reserves.

## Coop versus fight

A cooperative reading asks what White can still do if Black never answers.
A fighting reading asks whether White can force a completed road when Black
answers every White move with a flat. Those two readings disagree on several
rounds; the tournament card keeps them separate as `trap` versus `win`, and
reserves `fort` for rounds where even cooperation fails.
