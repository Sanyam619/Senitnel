# Contest rules

This booklet is a path-block contest on a Quoridor board. Black tries to
raise White's shortest path to the south edge up to the published floor.
White answers with pawn steps when the card asks for fighting play.

## Wall inventory

Each round ships a non-negative `walls_left` count for Black. Every legal
wall Black files spends one from that inventory. White never places walls
here.

## Orthogonal paths

Pawns step orthogonally to an empty neighboring square. They cannot cross a
wall segment and cannot land on the other pawn. Path length is the number
of steps in a shortest legal walk to that side's goal edge.

## Illegal cuts

A wall is illegal when it is off-board, overlaps or crosses an existing
wall segment, or — after it is placed — either pawn has no remaining
orthogonal path to its own goal. Classic Quoridor connectivity is required
at every placement.

## Shortest-path floors

The contest floor is documented in `path_floors.md`. Meeting the floor is
what counts as a successful block. Reported `path_len` values must be the
true shortest path after the filed line or cooperative plan — lengthening
a path on paper without changing the position is not allowed.

## Coop versus fight

A cooperative reading asks what Black can still do if White never moves.
A fighting reading asks whether Black can force the floor when White's pawn
answers every wall. Those two readings disagree on several rounds in this
booklet; the score card keeps them separate as `trap` versus `win`, and
reserves `fort` for rounds where even cooperation fails inside the wall
budget.
