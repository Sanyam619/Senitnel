# Patch-market contest rules

Every sheet under `/app/puzzles/` is one round of a two-player patch-market
game. You are the First player, **Red**. The opponent is **Blue**. The two of
you share one time track and one market of patches.

## The track and turn order

Both time tokens start at position 0 on a track that ends at the sheet's
`time_track` value. The player whose token is **further back** takes the next
turn. If the two tokens sit on the same position, the First player (Red) moves.
A token that has reached the end of the track never moves again. The round is
over once both tokens are at the end.

Because the player who is behind keeps moving, one side can take several turns in
a row before the other catches up. That is the tempo of the round.

## The two turn choices

On your turn you do exactly one of:

- **Advance.** Jump your token to one space past the other player's token
  (never beyond the end of the track). Bank one button for every space you moved.
- **Take a patch.** Choose any patch still in the market that you can afford
  (its button cost is at most your banked buttons), pay that cost, lay its
  polyomino on your quilt, remove it from the market, and push your token forward
  by the patch's time cost.

## Laying a patch

A patch is a polyomino printed in a fixed orientation (no rotation or
reflection). It must be placed fully inside the quilt and may not cover a blocked
cell or a cell already covered by one of your patches. Blue's quilt is not
tracked — Blue can always place whatever it takes, so Blue's takes only spend
buttons and time and remove patches from the shared market.

## Income

Income spots sit at the `income` positions on the track. Whenever your token
moves **onto or past** an income spot during a turn, bank buttons equal to the
total printed income of the patches already on your quilt. A patch you lay on
the same turn is on the quilt before the token moves, so its income counts for
spots crossed on that turn.

## Closing score and the floor

When the round ends, Red's score is:

    banked buttons  -  2 x (empty quilt cells)

Blocked cells are never empty and never usable, so they carry no penalty. Every
uncovered non-blocked cell costs two. The round's `floor` is the score Red is
trying to reach. Blue has no score of its own; Blue plays only to hold Red under
the floor.

## Verdicts

- **win** — Red can force a closing score at or above the floor against every
  Blue line, however Blue spends the shared market and tempo.
- **trap** — Red cannot force the floor, but Red does reach it when Blue only
  ever advances (an idle, non-contesting opponent).
- **fort** — Red cannot reach the floor even against a Blue that only advances.
