# Tournament card

Hand in the finished card at `/app/answers.json`. Names and spellings are case-sensitive.

## What the card must say

List every contest round under `boards`, ordered by `board_id` ascending from 1.

## How a round is judged

For every round, answer two separate questions:

1. **Can Black force capture of the marked defender piece when White fights to keep it on the board, within the stone budget below?** That is `status`.
2. **If White always passes, can Black still remove that marked piece?** That is `coop_capturable`.

### Force budget

A `win` must be a forced capture in at most **five Black stone plays** (colour-prefixed Black tries that are not `pass`). Longer Black hunts do not count as wins for this card even if a deeper search eventually takes the mark. Cooperative White-pass captures are scored only under `coop_capturable`.

### White fighting replies (exact)

When grading a forcing line, White’s available fighting replies are:

- If White is in check: every legal White move (the check must be answered).
- Otherwise: only (a) legal moves of the marked piece, and (b) legal captures by any White piece.

King shuffles that are not captures, and other non-mark quiet moves, are **not** fighting replies. On a winning `sequence`, White may play `pass` only when that fighting set is empty. Passing while a fighting reply exists is cooperative and is rejected. Arbitrary square-to-square tries that are not in the fighting set also fail the card even if a loose probe accepts them.

The submitted `sequence` must itself be forcing: after every Black stone in the line, every remaining White fighting reply must still leave Black able to finish within the leftover Black-stone budget. A capture that only works because White keeps choosing helpful replies is not a win.

Some open shapes fill when White cooperates and still count as unwinnable when White resists within the budget. A sensei whisper that only checks surface fillability can look cheerful on those shapes. That whisper is not the same rule as the refutation list below.

The marked piece starts on `target` in the round file. Fleeing off the target square without being captured does not finish the objective — the piece must leave the board.

### Fort shapes

If Black cannot remove the marked piece even when White always passes, the round is unwinnable with `coop_capturable` false and no `refutations`.

## Each round row

Every row carries `board_id`, `status`, and `coop_capturable`.

### Wins

Winning rounds set `status` to `win` and `coop_capturable` to `true` (if Black can force the capture under resistance within the budget, the cooperative-pass capture is also possible).

Add `sequence`: the forcing line as colour-prefixed moves with announce tags (`"black e2e4|silent"`, `"white e7e5|silent"`, `"black d5e4|taken:e4"`). Coordinates are standard algebraic.

Announce tags must match what the sealed judge would speak for that try:

- quiet legal try → `silent`
- check without capture → `check` (or `mate` if it is mate)
- capture on square `xy` → `taken:xy`
- capture that also checks → `taken:xy+check` (or `taken:xy+mate`)

Match logs under `/app/history/` show the live dialect, including the `taken:<sq>+check` compound form.

The table judge must accept every step and the marked piece must be captured at the end. The line must include at least two White plies (`"white …"`, including pass only when no fighting reply remains). At least one of those White plies must be a stone play (not pass). Winning lines need at least three Black stone plays (not pass).

### Unwinnable rounds

Skip `sequence`.

- If `coop_capturable` is false, skip `refutations` too (or leave them empty).
- If `coop_capturable` is true, add `refutations`: one White reply for each Black first-try covered by the threat rule in the next section. Each reply looks like `{"after_black": "<uci>", "white": "<uci>"}` or `{"after_black": "<uci>", "white": "pass"}`.

#### Which Black first-tries need a refutation

A Black first-try needs a refutation when, after that try, if White passes, Black can capture the marked piece off the board on Black's very next move. Immediate captures on the first try are already finished captures — they are not listed as refutation rows.

That is the whole list. Do not add first-tries that only work after a longer White-pass hunt (two or more further Black stones). The sensei whisper under `/app/tools/` can look cheerful on moves that are not refutation threats — do not copy the sensei's fillability reading onto the card.

For each pair, the two-move try `black …` then the listed White reply must be legal for the judge and must leave the marked piece still on the board. Every threat of the kind above must appear. Extra refutation rows are allowed when they also follow this threat rule and keep the piece on the board.

## Tiny shape sample

```json
{
  "boards": [
    {"board_id": 1, "status": "win", "coop_capturable": true, "sequence": ["black a2a3|silent", "white h1h2|silent", "black a3a4|silent", "white h2h3|silent", "black a4a8|taken:a8"]},
    {"board_id": 2, "status": "unwinnable", "coop_capturable": true, "refutations": [{"after_black": "c2c4", "white": "d4c2"}]},
    {"board_id": 3, "status": "unwinnable", "coop_capturable": false}
  ]
}
```
