# Contest rules

This booklet is a pin-and-surround contest on a Hive board laid out on
axial hex coordinates `(q, r)`. White tries to drop Black's queen freedom
down to the published floor. Black answers with insect moves when the card
asks for fighting play.

## Move inventory

Each round ships a `moves_left` count for White. Every legal move White
files spends one from that count. Black never spends from White's
inventory.

## One-hive rule

Every move, for either side, must keep the hive a single connected group
both before the mover lifts off and after it lands. A piece that is the
sole connection between two clusters cannot move. Landing squares must
also be reachable through an open gate: sliding into a hex requires at
least one of the two hexes it shares with the origin to be empty (a piece
cannot squeeze through a gap that is fully boxed in on both sides).

## Insect movement

- **Queen** — steps to one open, gate-legal adjacent hex.
- **Beetle** — steps to any adjacent hex, empty or occupied; landing on an
  occupied hex climbs on top and counts that hex as covered by the beetle,
  not by the piece underneath. A beetle on top of the hive can always
  climb down or across regardless of the one-hive check on the ground
  layer.
- **Grasshopper** — jumps in a straight line over one or more contiguous
  occupied hexes and lands on the first empty hex past them. It cannot
  move if there is no adjacent occupied hex in that direction.
- **Spider** — slides exactly three hexes around the outside of the hive,
  never lifting off contact with the hive and never revisiting a hex in
  the same move.
- **Ant** — slides any number of hexes around the outside of the hive to
  reach any other free hex on the perimeter, subject to the freedom floor
  documented in `freedom_floors.md`.

## Stacking

A hex's occupant for adjacency and freedom purposes is whichever piece
sits on top of its stack. A beetle-covered hex counts as occupied when
computing neighbor freedom, regardless of which piece is underneath.

## Freedom and the surround floor

The contest floor is documented in `freedom_floors.md`. Meeting the floor
is what counts as a successful surround. Reported `freedom` values must be
the judge's true count on the resulting position — claiming a lower number
without changing the position is not allowed.

## Coop versus fight

A cooperative reading asks what White can still do if Black never moves.
A fighting reading asks whether White can force the floor when Black
answers every move. Those two readings disagree on several rounds in this
booklet; the score card keeps them separate as `trap` versus `win`, and
reserves `fort` for rounds where even cooperation fails inside the move
budget.
