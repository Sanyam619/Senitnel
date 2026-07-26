# Freedom floors

`PIN_FLOOR = 0`.

A surround succeeds only when Black's queen has freedom at most zero —
every one of its six neighboring hexes is occupied (a beetle-covered
neighbor counts as occupied).

## What `freedom` must mean

- On a `win` row, play the filed `sequence` from the printed position. The
  true Black queen freedom afterward must equal the filed `freedom`, and
  that value must be at most the floor.
- On a `trap` row, `freedom` is the queen's freedom after a cooperative
  move-only plan that uses at most `moves_left` moves while Black stays
  put. That value must be at most the floor.
- On a `fort` row, `freedom` is the queen's current freedom on the printed
  sheet (no further moves).

## Padding is forbidden

Do not invent extra shuffles or phantom climbs to lower the reported
`freedom`. The filed number must match the value the table judge would
compute on the resulting position.

## ANT_FREEDOM_FLOOR

`ANT_FREEDOM_FLOOR = 2`.

An ant may only leave its current hex when that hex's own freedom (its
count of empty neighboring hexes before the move) is at least two. Below
that floor the ant is considered too pinched to unstick itself from the
perimeter and has no legal moves that round, even though every other
insect's leave-check only asks whether the hive stays connected.
