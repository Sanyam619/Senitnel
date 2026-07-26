# Score card

Hand in `/output/hive-card.json`. Spellings are case-sensitive.

## Top level

- `schema_tag` must be exactly `hive-pin-v1`.
- `rounds` lists every booklet board, ordered by `board_id` ascending
  (`board_01`, `board_02`, … `board_10`).

## Each round row

| Field | Meaning |
| --- | --- |
| `board_id` | Round name matching the puzzle file stem. |
| `status` | `win`, `trap`, or `fort` under the rules below. |
| `coop_pin` | Whether White can still finish the surround if Black stops moving. |
| `key_bug` | On `win`: one legal first move of a forcing line, as a move token. On `trap` / `fort`: `""`. |
| `freedom` | Black queen's true freedom after the filed sequence (or the coop plan / current position). Must equal the judge's count — padding is forbidden. |
| `sequence` | On `win`: move tokens for one forcing line. On `trap` / `fort`: `[]`. |
| `refutations` | On `trap`: `{ "move", "reply" }` coverage for every threat move. On `win` / `fort`: `[]`. |

## PIN_FLOOR

A successful surround means Black's queen has freedom at most **0**
(`PIN_FLOOR = 0`) — every one of its six neighboring hexes is occupied.
`freedom` on a `win` must meet that floor after the sequence; on a `trap` it
is Black's queen freedom after a cooperative move plan of length at most
`moves_left` (Black passes); on a `fort` it is the current freedom with no
further White moves.

## How a round is scored

Every round is White to move. White plays moves (spending `moves_left`).
Black answers only when the fight matters. Two questions decide the row:

1. **Can White force the queen's freedom to the floor against fighting
   Black?**
2. **If Black never moves, can White still reach the floor with at most
   `moves_left` legal moves?**

### win

White to move can force the queen's freedom to the floor no matter how
Black answers. Set `status` to `win` and `coop_pin` to `true`.

Fill `key_bug` with one legal first move that keeps the force. Fill
`sequence` with a line of move tokens starting from that first move; after
the line, the queen's true freedom equals `freedom` and is at most the
floor. Leave `refutations` empty.

An immediate legal move that alone drops the freedom to the floor is a
`win`. Longer forcing lines (White move, Black reply, White move, …) are
also `win` when every Black answer still leaves White able to finish the
surround within the remaining move budget.

### trap

White cannot force the floor against fighting Black, yet a move-only plan
still works if Black passes. Set `status` to `trap` and `coop_pin` to
`true`. Leave `key_bug` empty and `sequence` empty. Set `freedom` to the
queen's freedom after that cooperative plan (≤ `moves_left` moves).

A surface reading that only asks whether one White piece can reach an
empty queen-neighbor "looks pinned" often says yes on every trap. That
reading is the sensei whisper, and it is not the verdict: the round is
still a `trap`, not a `win`, because Black fights.

#### Threat moves and refutation coverage

A White first move **threatens** when:

1. that move alone does **not** drop the queen's freedom to the floor, and
2. there exists a second legal White move `M2` such that, with Black still
   on the same layout, `M` then `M2` drops the freedom to the floor.

For every threatening first move, `refutations` must carry a Black reply
that answers it: a legal Black move such that after White plays the threat
move and Black answers, **no** second move `M2` reaches the floor.

Each row is `{"move": "<move token>", "reply": "<move token>"}`. Every
required threat must appear (required ⊆ submitted). Extra rows are allowed
when they follow the same threat-and-answer rule. A first move that alone
hits the floor is a finished surround, not a threat row.

### fort

Even if Black never moves, no legal move sequence of length ≤ `moves_left`
reaches the floor. Set `status` to `fort` and `coop_pin` to `false`. Leave
`key_bug`, `sequence`, and `refutations` empty. Set `freedom` to the current
queen freedom.

## Tiny shape sample

```json
{
  "schema_tag": "hive-pin-v1",
  "rounds": [
    {"board_id": "board_01", "status": "win", "coop_pin": true,
     "key_bug": "W-G1>1,0", "freedom": 0,
     "sequence": ["W-G1>1,0"], "refutations": []},
    {"board_id": "board_02", "status": "trap", "coop_pin": true,
     "key_bug": "", "freedom": 0, "sequence": [],
     "refutations": [{"move": "W-B1>0,-1", "reply": "B-S1>-1,-2"}]},
    {"board_id": "board_03", "status": "fort", "coop_pin": false,
     "freedom": 2, "key_bug": "", "sequence": [], "refutations": []}
  ]
}
```

The sample moves and freedom values are illustrative only — they are not
booklet answers.
