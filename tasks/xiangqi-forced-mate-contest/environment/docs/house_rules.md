# House rules graded on this booklet

These are the Xiangqi constraints the sealed judge enforces. Surface helpers
that skip any of them are not authoritative for the card.

## Palace

The general and the advisors stay inside their 3×3 palace (files `d`–`f`;
Red ranks `0`–`2`, Black ranks `7`–`9`). A draft that walks an advisor or
general outside the palace is illegal even if a printer stamps it.

## Horse hobble

A horse leaps one step orthogonally then one step diagonally, but the
adjacent orthogonal "hobble" square must be empty. A leap through an occupied
hobble square is illegal. A whisper that ignores hobble will invent mates that
the table never allows.

## Cannon screens

A cannon slides like a chariot on an empty line. To capture, it needs
**exactly one** screen between itself and the target. Zero screens or two or
more screens means the capture does not land.

## River

Elephants cannot cross the river (between ranks `4` and `5`). Soldiers move
only forward until they cross; afterward they may also step sideways. The
card's `river_cross` flag cares about whether a filed win line carries any
piece across that river boundary.

## Facing generals

The two generals may not stand on the same file with an empty path between
them. A try that opens that corridor is illegal.

## Mate-length floor

Forced wins for this booklet are at most three Red plies. Longer forced mates
are out of scope for `win`. Cooperative mates use the same three-ply ceiling.
Padding a shorter forced mate to a larger `mate_in` fails grading.
