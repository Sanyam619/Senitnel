# House rules for the tile-meeple rounds

## Play at this table

Carcassonne on a 3x3 grid (`a1`…`c3`). Cells use letter-number names; Red moves
first on every sheet. Each sheet lists a **hand** of pre-oriented tiles. Tiles
are placed as written — the desk does not rotate them. A Red turn places one
hand tile on an empty cell that touches the living landscape and matches every
touching edge, and may seat one meeple on a feature of that new tile.

## Edges and features

Each tile lists four edges north-east-south-west using `C` (city), `R` (road),
or `F` (field). A trailing `*` is a pennant on a city tile. A `#` marks a
cloister. Cities join across matching `C` edges; roads join across matching
`R` edges. Field regions join across matching `F` edges. The outer rim stays
open: a city or road that faces the void never finishes.

## Meeples and contested claims

A meeple seats as `city`, `road`, `cloister`, or `farm` on an edge (`N`/`E`/`S`/
`W`) or `C` for a cloister. When a feature finishes, only a sole-Red claim
scores. If Blue also has a meeple on that feature, Red scores nothing from it,
and that city does not feed farmer scoring.

Blue's fighting reply is a `seat:cell:kind:edge` from Blue's remaining stock,
or `pass` when Blue sits still. Friendly lines are Red alone.

## Scoring and the floor

- Finished sole-Red city: `2` per tile in the city, plus `2` per pennant.
- Finished sole-Red road: `1` per tile.
- Finished sole-Red cloister: `1` plus the number of neighbouring tiles on the
  board.
- Farmer majority: each sole-Red farm scores `3` for every finished sole-Red
  city it touches (same tile or an orthogonal neighbour).

`score_delta` is Red's running score after the filed line. The sheet's
`floor:` line is the house target. Red gets at most three turns on a line.

## Verdict words

- `win` — Red forces the floor inside three Red turns no matter how Blue seats.
- `trap` — Blue can hold the floor off under a fight, but Red still reaches it
  inside three Red turns once Blue stops fighting.
- `fort` — the floor stays out of reach even with Blue sitting still for three
  Red turns.

`coop_claim` is true exactly when the friendly climb exists inside three Red
turns (so `win` and `trap` carry `true`, `fort` carries `false`).

## Threats and refutations

On `trap` rounds a Red first placement **threatens** when it does not itself
meet the floor, yet Red would meet the floor on Red's very next turn if Blue
did nothing. Each threat needs one Blue reply that answers it: a legal Blue
seat after which Red cannot meet the floor on the following single Red turn.

Each refutation row is
`{"placement": "<the Red try>", "reply": "<the Blue answer>"}`. Every
threatening first placement must appear (the required set must be a subset of
what you submit). Extra rows are allowed when they follow the same
threat-and-answer rule.

## Move dialect

Red: `FFCF@b3:0+city:S` or `FFCF@b3:0` (no meeple). Blue: `seat:b2:city:N` or
`pass`. Sequence steps carry a colour word: `red …` or `blue …`.

The overnight kiosk prints `win` wherever a fourth cooperative Red turn
reaches the floor, and the sensei whisper cheers city and road fill without
reading farmer majority. Neither reads Blue's fighting seats.
