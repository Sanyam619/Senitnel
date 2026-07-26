# Score card

Hand in `/output/quoridor-card.json`. Spellings are case-sensitive.

## Top level

- `schema_tag` must be exactly `quoridor-path-v1`.
- `rounds` lists every booklet board, ordered by `board_id` ascending
  (`board_01`, `board_02`, … `board_11`).

## Each round row

| Field | Meaning |
| --- | --- |
| `board_id` | Round name matching the puzzle file stem. |
| `status` | `win`, `trap`, or `fort` under the rules below. |
| `coop_block` | Whether Black can still push White's shortest path to the floor if White stops moving. |
| `key_wall` | On `win`: one legal first wall of a forcing line. On `trap` / `fort`: `""`. |
| `path_len` | White's shortest path length after the filed sequence (or the coop wall plan / current path). Must equal the true shortest path — padding is forbidden. |
| `sequence` | On `win`: tokens `wall:<id>` and `pawn:<cell>` for one forcing line. On `trap` / `fort`: `[]`. |
| `refutations` | On `trap`: `{ "move", "reply" }` coverage for every threat wall. On `win` / `fort`: `[]`. |

## PATH_FLOOR

A successful block means White's shortest orthogonal path to the south edge
is at least **7** (`PATH_FLOOR = 7`). `path_len` on a `win` must meet that
floor after the sequence; on a `trap` it is White's path after a cooperative
wall-only plan of length at most `walls_left`; on a `fort` it is the current
White path with no further walls.

## How a round is scored

Every round is Black to move. Black places walls (spending `walls_left`).
White answers only with pawn steps in this booklet. Two questions decide the
row:

1. **Can Black force White's shortest path ≥ 7 against fighting White?**
2. **If White never moves, can Black still reach path ≥ 7 with at most
   `walls_left` legal walls?**

### win

Black to move can force White's shortest path ≥ 7 no matter how White's pawn
answers. Set `status` to `win` and `coop_block` to `true`.

Fill `key_wall` with one legal first wall that keeps the force. Fill
`sequence` with a line of `wall:…` / `pawn:…` tokens starting from that first
wall; after the line, White's true shortest path equals `path_len` and is at
least 7. Leave `refutations` empty.

An immediate legal wall that alone lifts the path to ≥ 7 is a `win`. Longer
forcing lines (Black wall, White pawn reply, Black wall, …) are also `win`
when every White answer still leaves Black able to finish the block within
the remaining wall inventory.

### trap

Black cannot force the floor against fighting White, yet a wall-only plan
still works if White passes. Set `status` to `trap` and `coop_block` to
`true`. Leave `key_wall` empty and `sequence` empty. Set `path_len` to White's
shortest path after that cooperative wall plan (≤ `walls_left` walls).

A surface reading that only asks whether blocking the first step of White's
current corridor "looks blocked" often says yes on every trap. That reading
is the sensei whisper, and it is not the verdict: the round is still a
`trap`, not a `win`, because White fights.

#### Threat walls and refutation coverage

A Black first wall **threatens** when:

1. that wall alone does **not** make White's path ≥ 7, and
2. there exists a second legal wall `W2` such that, with White still on the
   same square, `W` then `W2` makes White's path ≥ 7.

For every threatening first wall, `refutations` must carry a White pawn
reply that answers it: a legal one-step White move to a square `reply` such
that after Black plays the threat wall and White steps to `reply`, **no**
second wall `W2` achieves path ≥ 7.

Each row is `{"move": "<wall id>", "reply": "<White square>"}`. Every
required threat must appear (required ⊆ submitted). Extra rows are allowed
when they follow the same threat-and-answer rule. A first wall that alone
hits the floor is a finished block, not a threat row.

### fort

Even if White never moves, no legal wall sequence of length ≤ `walls_left`
reaches path ≥ 7. Set `status` to `fort` and `coop_block` to `false`. Leave
`key_wall`, `sequence`, and `refutations` empty. Set `path_len` to White's
current shortest path.

## Tiny shape sample

```json
{
  "schema_tag": "quoridor-path-v1",
  "rounds": [
    {"board_id": "board_01", "status": "win", "coop_block": true,
     "key_wall": "h-b2", "path_len": 7,
     "sequence": ["wall:h-b2"], "refutations": []},
    {"board_id": "board_02", "status": "trap", "coop_block": true,
     "key_wall": "", "path_len": 7, "sequence": [],
     "refutations": [{"move": "h-b2", "reply": "c4"}]},
    {"board_id": "board_03", "status": "fort", "coop_block": false,
     "key_wall": "", "path_len": 5, "sequence": [], "refutations": []}
  ]
}
```

The sample walls and lengths are illustrative only — they are not booklet
answers.
