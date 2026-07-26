# Contest rules

This booklet is a mill-fork contest on a classic Nine Men's Morris board.
White tries to close a mill inside each round's move budget. Black answers
with legal slides or flights when the card asks for fighting play.

## The board

Twenty-four points linked in three concentric squares with mid-side
crossbars. A mill is any marked line of three points of the same colour.
The point names and mill lines are in `board_format.md`.

## Move inventory

Each round ships a `moves_left` count for White. Every completed White turn
(slide or flight, plus any removals that mill required) spends one from that
count. Black never spends from White's inventory.

## Phases

Men slide along an edge to an empty adjacent point. When a side has three
or fewer men left, that side may **fly**: move a man to any empty point on
the board. Flying does not change mill detection or removal rules.

## Closing a mill and removing

Landing so that one or more mills are completed obliges that side to remove
an opposing man for each mill completed on that landing. A removal may not
take a man that sits in an opposing mill unless every opposing man is
already in a mill. The sealed judge enforces that restriction.

## Mill-count floor

A successful mill for this contest means White forms at least **one** mill
(`MILL_FLOOR = 1`) inside the move budget. Reported `mill_in` values must
equal the true number of mills White completed on the filed line — padding
with reversible swings that form and then undo mills is not allowed.

## Coop versus fight

A cooperative reading asks what White can still do if Black never moves.
A fighting reading asks whether White can force a mill when Black answers
every move. Those two readings disagree on several rounds in this booklet;
the score card keeps them separate as `trap` versus `win`, and reserves
`fort` for rounds where even cooperation fails inside the move budget.
