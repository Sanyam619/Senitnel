# House rules for the corner-contact rounds

## Play at this table

Blokus packing on a 5×5 grid. Blue moves first on every booklet sheet. Each
colour keeps a remaining piece inventory printed on the sheet (`blue_inv` /
`yellow_inv`). A turn spends one inventory piece and stamps its squares onto
empty cells.

Same-colour pieces must touch at corners only: a new piece must share at least
one diagonal corner with an already-placed square of its colour, and must not
share an orthogonal edge with any same-colour square. Opposite colours may
share edges freely. `X` cells are permanent blocks. When a colour has no
squares on the board yet, its first piece must cover one of the four board
corners.

This booklet never asks you to play a full Blokus match to exhaustion. It asks
whether Blue can force the inventory floor inside a short Blue-placement budget.

## Squares-left floor

`squares_left` is the total number of squares still sitting in Blue's remaining
inventory (sum of piece sizes). The house **squares-left floor** is 0: the fill
succeeds the moment Blue's inventory is empty (`squares_left <= 0`), including
after a Yellow reply that Blue forced into a dead end.

Piece sizes on this table: `1`=1, `2`=2, `I3`/`V3`=3, `I4`/`O4`/`T4`/`L4`/`S4`=4.

## Three Blue placements

Blue gets at most three placements on a line. Yellow's replies in between are
free and never count against those three. On a `win` line Yellow fights: every
legal Yellow placement is allowed, and Yellow passes only when it truly has
nothing legal. On a friendly line Yellow sits still (Blue plays consecutive
placements).

## Verdict words

- `win` — Blue forces the squares-left floor inside three Blue placements no
  matter how Yellow fights.
- `trap` — Yellow can hold the floor off under a fight, but Blue still reaches
  it inside three Blue placements once Yellow stops fighting.
- `fort` — the floor stays out of reach even with Yellow sitting still for three
  Blue placements.

A round is one of the three, never two. A friendly fill is not a win: most
rounds where Blue can empty the inventory with Yellow sitting still are rounds
where one Yellow reply breaks the climb.

`coop_fill` is true exactly when the friendly climb exists inside three Blue
placements (so `win` and `trap` carry `true`, `fort` carries `false`).

## Threats and refutations

On `trap` rounds a Blue first placement is an **inventory-wasting threat** when
it does not itself meet the floor, yet Blue would meet the floor on Blue's very
next placement if Yellow did nothing. Each threat needs one Yellow reply that
answers it: a legal Yellow placement after which Blue cannot meet the floor on
the following single Blue placement.

Each refutation row is
`{"piece_id": "<Blue piece of the try>", "reply": "<Yellow placement>"}` with
the dialect below. Every threatening first placement must be covered (the
required set of Blue piece_ids paired with a defeating reply must be a subset of
what you submit — for each graded threat there exists a submitted row whose
`piece_id` matches and whose `reply` defeats that threat). Extra rows are
allowed when they follow the same threat-and-answer rule. A Blue try that meets
the floor outright is a finished fill, not a threat row.

## Placement dialect

A placement is written `V3@b2,b3,c3` — piece id, then the occupied squares in
file-rank order joined by commas (the sealed judge accepts any square order and
normalizes). Sequence steps carry a colour word: `blue V3@b2,b3,c3` or
`yellow 2@a1,b1`.

Card fields `piece_id` and `placement` split that token: on `win` / `trap`,
`piece_id` is the piece of the first Blue step and `placement` is the
`@`-suffix squares string (e.g. `b2,b3,c3`). On `fort` both are empty strings.

The overnight kiosk prints `win` wherever a fourth cooperative Blue placement
reaches the floor, and the sensei whisper cheers when a piece's axis-aligned
bounding box fits on empty cells — including placements that share an edge with
Blue. Neither reads Yellow's fighting replies.
