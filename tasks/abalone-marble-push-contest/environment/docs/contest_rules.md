# House rules for the marble-push rounds

## Play at this table

Abalone on a hex board of radius 2 (nineteen cells). Cells use letter-number
names (`a1`…`e5`) that stay on the hex; off-hex letter-number pairs are not
cells. Black moves first on every sheet. A turn moves one contiguous group of
one, two, or three of your own marbles one step in a single hex direction.

## Inline pushes and sumito

An **inline** turn slides the group along its own line. The cell ahead of the
front marble must be empty (a march) or hold enemy marbles that you are allowed
to push (a sumito). Sumito strength on this table:

- two of yours may push exactly one enemy
- three of yours may push one or two enemies
- equal counts never push; a shorter line never pushes a longer one
- you never push three enemies

When the cell beyond the enemy line is empty, the enemies shift one step. When
that beyond-cell is off the board, those enemy marbles are **ejected**. Your
own marbles must finish on the board — walking your front marble off with no
legal sumito is a forbidden suicide push and is illegal.

## Side-steps

A **side-step** slides a line of two or three sideways (not along the line).
Every destination cell must be on the board and empty. Side-steps never eject.

## Ejection floor and three Black turns

`ejected` counts White marbles pushed off during the filed sequence. The house
**ejection floor** is 1: the push succeeds the moment `ejected >= 1`.

Black gets at most three turns on a line. White's replies in between are free
and never count against those three. On a `win` line White fights: every legal
White reply is allowed, and White passes only when it truly has nothing legal.
On a friendly line White sits still (Black plays consecutive turns).

## Verdict words

- `win` — Black forces the ejection floor inside three Black turns no matter
  how White fights.
- `trap` — White can hold the floor off under a fight, but Black still reaches
  it inside three Black turns once White stops fighting.
- `fort` — the floor stays out of reach even with White sitting still for three
  Black turns.

A round is one of the three, never two. A friendly ejection is not a win: most
rounds where Black can climb the floor with White sitting still are rounds
where one White reply breaks the climb.

`coop_eject` is true exactly when the friendly climb exists inside three Black
turns (so `win` and `trap` carry `true`, `fort` carries `false`).

## Threats and refutations

On `trap` rounds a Black first turn **threatens** (an over-push try) when it
does not itself meet the floor, yet Black would meet the floor on Black's very
next turn if White did nothing. Each threat needs one White reply that answers
it: a legal White turn after which Black cannot meet the floor on the following
single Black turn.

Each refutation row is `{"move": "<the Black try>", "reply": "<the White
answer>"}` with the move dialect below. Every threatening first turn must
appear (the required set must be a subset of what you submit). Extra rows are
allowed when they follow the same threat-and-answer rule. A Black try that
meets the floor outright is a finished ejection, not a threat row.

## Move dialect

A turn is written by naming the moving group rear-to-front, then `>`, then the
cell the front marble steps into — for example `c3d3>e3` (two-marble inline) or
`c3>d3` (single marble). Side-steps use the same spelling: the body lists the
line in order and the landing is where the first named marble goes. Sequence
steps carry a colour word: `black c3d3>e3` or `white e1>d1`.

The overnight kiosk prints `win` wherever a fourth cooperative Black turn
reaches the floor, and the sensei whisper cheers when a line looks contiguous —
including illegal 2-vs-3 sumito shapes. Neither reads White's fighting replies.
