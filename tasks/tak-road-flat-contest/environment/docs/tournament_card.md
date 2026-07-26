# Tournament card

Hand in the finished card at `/app/answers.json`. Names and spellings are case-sensitive.

## What the card must say

Keep `schema_tag` as `tak-road-v1`. List every contest round under `rounds`,
ordered by `board_id` ascending (`board_01` … `board_11`).

## How a round is judged

Every round is White to move. Black answers only with flat placements in this
booklet. Two questions decide the row:

1. **Can White force a completed north-south road against fighting Black?**
2. **If Black never moves, can White still complete a road with the remaining
   reserves and legal slides?**

### Road floor

A completed White road is a north-south orthogonal chain of White road stones
(flats and the White capstone). Standing stones never count. The published
floor is **5**: `road_len` on a `win` must meet that floor after the sequence;
on a `trap` it is the road length after a cooperative White-only plan; on a
`fort` it is `0` when no road exists.

### win

White can finish the road on this turn, or White has a first move after which
every legal Black flat answer still leaves at least one legal White move that
finishes the road. The finishing reply may be a placement or a slide. A single
unblockable slide finish counts just as much as two open placement finishes.
Set `status` to `win` and `coop_road` to `true`.

Fill `key_square` with the square of one forcing first move. Fill `sequence`
with one legal line starting from that move. For a road that takes two White
turns, include a legal Black flat between White's first move and finishing
move. After the line, White's true shortest road equals `road_len` and is at
least 5. Leave `refutations` empty.

### trap

White cannot force the road against fighting Black, yet a White-only plan still
works if Black passes. Set `status` to `trap` and `coop_road` to `true`. Leave
`key_square` empty and `sequence` empty. Set `road_len` to the road length after
that cooperative plan.

A surface reading that ignores the carry limit or treats standing tops as road
stones often says the lane is ready on every trap. That reading is the sensei
whisper, and it is not the verdict: the round is still a `trap`, not a `win`,
because Black fights.

#### Threat moves and refutation coverage

A White first move **threatens** when:

1. that move alone does **not** complete a road, and
2. there exists a second legal White move such that, with Black still passing,
   the second move completes a north-south road.

For every threatening first move, `refutations` must carry a Black flat reply
that answers it: after White plays the threat and Black places that flat,
**no** second White move completes a road.

Each row is `{"move": "<White threat token>", "reply": "<Black flat token>"}`.
Every required threat must appear (required ⊆ submitted). Extra rows are
allowed when they follow the same threat-and-answer rule. A first move that
alone completes the road is a finished road, not a threat row.

### fort

Even if Black never moves, no legal White plan completes a road. Set `status`
to `fort` and `coop_road` to `false`. Leave `key_square`, `sequence`, and
`refutations` empty. Set `road_len` to `0`.

## Each round row

| Field | Meaning |
| --- | --- |
| `board_id` | Round name matching the puzzle file stem. |
| `status` | `win`, `trap`, or `fort` under the rules above. |
| `coop_road` | Whether White can still finish a north-south road if Black never answers. |
| `key_square` | On `win`: the square named by one forcing first move (placement square, or slide origin). On `trap` / `fort`: `""`. |
| `road_len` | White's shortest north-south road length after the filed sequence (or after a cooperative plan / current position). Must equal the true shortest road — padding is forbidden. |
| `sequence` | On `win`: move tokens for one forcing line. On `trap` / `fort`: `[]`. |
| `refutations` | On `trap`: `{ "move", "reply" }` coverage for every threat first move. On `win` / `fort`: `[]`. |
