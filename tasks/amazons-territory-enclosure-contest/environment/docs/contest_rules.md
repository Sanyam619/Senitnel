# House rules for the territory enclosure rounds

## Play at this table

Game of the Amazons on a 5x5 board. On a turn a player chooses one of their
amazons, slides it any number of empty squares like a chess queen (orthogonal
or diagonal, no jumping), then from the arrival square shoots one arrow the
same way onto an empty square. The arrow stays forever and blocks every later
queen path. The square the amazon left becomes empty and may receive the arrow
when the path is clear.

A side with no legal turn is stuck. This booklet never asks you to play out a
full game to exhaustion — it asks whether White can force a territory floor
inside a short budget.

## Exclusive territory

From either colour, walk every empty square that colour's amazons can reach by
queen moves through empties only (arrows and amazons of either colour block).
An empty square that only White can reach is White exclusive territory; an
empty square that only Black can reach is Black exclusive territory. Shared
empties count for neither.

`territory_delta` is White exclusive minus Black exclusive. The house
**territory floor** is 2: the enclosure succeeds the moment
`territory_delta >= 2`, including after a Black reply that White forced into a
self-block.

## Three White turns

White gets at most three turns on a line. Black's replies in between are free
and never count against those three. On a `win` line Black fights: every legal
Black reply is allowed, and Black passes only when it truly has nothing legal.
On a friendly line Black sits still (White plays consecutive turns).

## Verdict words

- `win` — White forces the territory floor inside three White turns no matter
  how Black fights.
- `trap` — Black can hold the floor off under a fight, but White still reaches
  it inside three White turns once Black stops fighting.
- `fort` — the floor stays out of reach even with Black sitting still for three
  White turns.

A round is one of the three, never two. A friendly enclosure is not a win:
most rounds where White can climb the floor with Black sitting still are
rounds where one Black reply breaks the climb.

`coop_enclose` is true exactly when the friendly climb exists inside three
White turns (so `win` and `trap` carry `true`, `fort` carries `false`).

## Threats and refutations

On `trap` rounds a White first turn **threatens** when it does not itself meet
the floor, yet White would meet the floor on White's very next turn if Black
did nothing. Each threat needs one Black reply that answers it: a legal Black
turn after which White cannot meet the floor on the following single White
turn.

Each refutation row is `{"move": "<the White try>", "reply": "<the Black
answer>"}` with the move dialect below. Every threatening first turn must
appear (the required set must be a subset of what you submit). Extra rows are
allowed when they follow the same threat-and-answer rule. A White try that
meets the floor outright is a finished enclosure, not a threat row.

## Move dialect

A turn is written `a4-b3/c2` — amazon from `a4` to `b3`, arrow to `c2`. Sequence
steps carry a colour word: `white a4-b3/c2` or `black d1-d2/e2`. There is no
flip-count announce on this table.

The overnight kiosk prints `win` wherever a fourth cooperative White turn
reaches the floor, and the sensei whisper cheers when the board still shows
many empty squares. Neither reads Black's fighting replies.
