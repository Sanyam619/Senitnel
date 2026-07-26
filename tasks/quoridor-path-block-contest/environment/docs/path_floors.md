# Path floors

`PATH_FLOOR = 7`.

A block succeeds only when White's shortest orthogonal path to the south
edge is at least seven steps.

## What `path_len` must mean

- On a `win` row, play the filed `sequence` from the printed position. The
  true White shortest path afterward must equal the filed `path_len`, and
  that value must be ≥ 7.
- On a `trap` row, `path_len` is White's shortest path after a cooperative
  wall-only plan that uses at most `walls_left` walls while White stays
  put. That value must be ≥ 7.
- On a `fort` row, `path_len` is White's current shortest path on the
  printed sheet (no further walls).

## Padding is forbidden

Do not invent extra pawn zig-zags or phantom walls to inflate `path_len`.
The filed number must match the shortest legal path the table judge would
compute on the resulting position. Longer walks that ignore a shorter
route do not count.
