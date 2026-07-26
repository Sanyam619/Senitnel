# House rules for the zugzwang rounds

## Play at this table

Standard Connect Four on a 6×7 board. Discs fall under gravity: a drop names a
column `0`..`6` (left to right) and lands on the lowest empty row `0`..`5`
(bottom to top). Yellow moves first on every booklet sheet. Four of the same
colour in a row — orthogonal or diagonal — ends the line for that colour.

This booklet never asks you to play a full game to a clogged grid. It asks
whether Yellow can force a connect-four inside a short Yellow-drop budget, and
how odd/even threat parity and zugzwang shape the reading when Red fights.

## Odd and even threats

A **threat** for a colour is an empty cell that would complete four for that
colour if filled. Only the gravity landing of a column is playable on a turn.
House rows are numbered `1`..`6` from the bottom: an odd-row threat favors the
player to move (Yellow on these sheets); an even-row threat favors the
sitting side (Red). Positions where every useful Yellow try gifts Red an
even-threat finish — or otherwise leaves Yellow with no safe drop — are the
zugzwang draws in this booklet.

## Five Yellow drops

Yellow gets at most five drops on a filed line. Red's replies in between are
free and never count against those five. On a `win` line Red fights: every
legal Red reply is allowed, and Red passes only when the column set is empty.
On a friendly line Red sits still (Yellow plays consecutive drops).

## Verdict words

- `win` — Yellow forces a connect-four inside five Yellow drops no matter how
  Red fights.
- `trap` — Red can hold the connect off under a fight, but Yellow still
  connects inside five Yellow drops once Red stops fighting.
- `draw` — the connect stays out of reach even with Red sitting still for five
  Yellow drops (parity / zugzwang hold).

A round is one of the three, never two. A friendly connect is not a win: most
rounds where Yellow can climb to four with Red sitting still are rounds where
one Red reply breaks the climb.

`coop_win` is true exactly when the friendly climb exists inside five Yellow
drops (so `win` and `trap` carry `true`, `draw` carries `false`).

## Threats and refutations

On `trap` rounds a Yellow first drop **threatens** when it does not itself
connect four, yet Yellow would connect on Yellow's very next drop if Red did
nothing. Each threat needs one Red reply that answers it: a legal Red drop
after which Yellow cannot connect on the following single Yellow drop.

Each refutation row is `{"column": <Yellow try>, "reply": <Red answer>}` with
integer columns. Every threatening first drop must appear (the required set
must be a subset of what you submit). Extra rows are allowed when they follow
the same threat-and-answer rule. A Yellow try that connects outright is a
finished win line, not a threat row.

On `draw` rounds the graded set is every Yellow first drop that lets Red
connect four on Red's immediate reply. Each such losing try needs a refutation
row naming that Red finishing column. Trap-style one-ply threats, when they
exist under a longer cooperative hunt, also need answers.

## Move dialect

A drop is written with a colour word and a column: `yellow 3` or `red 0`.
Sequence steps are those strings in play order. There is no announce suffix on
this table.

The overnight kiosk prints `win` wherever a longer cooperative Yellow hunt
reaches four, and the sensei whisper only lists which columns still have room.
Neither reads Red's fighting replies or odd/even ownership.
