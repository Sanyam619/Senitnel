# Score card

Hand in `/output/morris-card.json`. Spellings are case-sensitive.

## Top level

- `schema_tag` must be exactly `morris-mill-v1`.
- `rounds` lists every booklet board, ordered by `board_id` ascending
  (`board_01` … `board_10`).

## Each round row

| Field | Meaning |
| --- | --- |
| `board_id` | Round name matching the puzzle file stem. |
| `status` | `win`, `trap`, or `fort` under the rules below. |
| `coop_fork` | Whether White can still close a mill if Black stops moving. |
| `key_point` | On `win`: the point White occupies to close the decisive mill. On `trap` / `fort`: `""`. |
| `mill_in` | True mill count White completed on the filed plan (see floor). |
| `sequence` | On `win`: move tokens for one forcing line. On `trap` / `fort`: `[]`. |
| `removals` | On `win`: Black points removed, in mill order. On `trap` / `fort`: `[]`. |
| `refutations` | On `trap`: `{ "move", "reply" }` coverage for every threat. On `win` / `fort`: `[]`. |

## MILL_FLOOR

A successful mill means White completes at least **1** mill
(`MILL_FLOOR = 1`). `mill_in` on a `win` is the true mill count along the
forcing line; on a `trap` it is the true mill count along a cooperative
plan of length at most `moves_left` (Black passes); on a `fort` it is `0`.
Inflating `mill_in` above the mills actually formed is refused.

## How a round is scored

Every round is White to move. White plays turns (spending `moves_left`).
Black answers only when the fight matters. Two questions decide the row:

1. **Can White force a mill against fighting Black?**
2. **If Black never moves, can White still close a mill with at most
   `moves_left` legal turns?**

### win

White to move can force a mill no matter how Black answers. Set `status`
to `win` and `coop_fork` to `true`.

Fill `key_point` with the closing point of the decisive mill. Fill
`sequence` with move tokens for one forcing line (White moves, Black
replies, …). Fill `removals` with the Black points taken after each White
mill on that line, in order. Set `mill_in` to the true mill count on the
line. Leave `refutations` empty.

An immediate legal turn that alone closes a mill is a `win`. Longer
forcing lines are also `win` when every Black answer still leaves White
able to finish inside the remaining move budget.

### trap

White cannot force a mill against fighting Black, yet a move-only plan
still works if Black passes. Set `status` to `trap` and `coop_fork` to
`true`. Leave `key_point`, `sequence`, and `removals` empty. Set `mill_in`
to the true mill count of that cooperative plan (≤ `moves_left` turns).

A surface reading that only asks whether one White man can step onto a
mill hole often says yes on every trap. That reading is the sensei
whisper, and it is not the verdict: the round is still a `trap`, not a
`win`, because Black fights — including by flying onto the hole when
Black is down to three men.

#### Threat moves and refutation coverage

A White first move **threatens** when:

1. that turn alone does **not** close a mill, and
2. there exists a second legal White turn such that, with Black still on
   the same layout (Black passed), the first turn then the second closes
   a mill.

For every threatening first move, `refutations` must carry a Black reply
that answers it: a legal Black move such that after White plays the threat
and Black answers, **no** single White follow-up closes a mill.

Each row is `{"move": "<move token>", "reply": "<move token>"}`. Every
required threat must appear (required ⊆ submitted). Extra rows are allowed
when they follow the same threat-and-answer rule. A first turn that alone
closes a mill is a finished mill, not a threat row.

### fort

Even if Black never moves, no legal White plan of length ≤ `moves_left`
closes a mill. Set `status` to `fort` and `coop_fork` to `false`. Leave
`key_point`, `sequence`, `removals`, and `refutations` empty. Set
`mill_in` to `0`.

## Tiny shape sample

```json
{
  "schema_tag": "morris-mill-v1",
  "rounds": [
    {"board_id": "board_41", "status": "win", "coop_fork": true,
     "key_point": "g7", "mill_in": 1,
     "sequence": ["W:g4-g7"], "removals": ["b6"], "refutations": []},
    {"board_id": "board_42", "status": "trap", "coop_fork": true,
     "key_point": "", "mill_in": 1, "sequence": [], "removals": [],
     "refutations": [{"move": "W:f4-g4", "reply": "B:c5-g7"}]},
    {"board_id": "board_43", "status": "fort", "coop_fork": false,
     "key_point": "", "mill_in": 0, "sequence": [], "removals": [],
     "refutations": []}
  ]
}
```

The sample moves and mill counts are illustrative only — they are not
booklet answers.
