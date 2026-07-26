# Score card

Hand in `/output/hex-card.json`. Spellings are case-sensitive.

## Top level

- `schema_tag` must be exactly `hex-shore-v1`.
- `rounds` lists every booklet board, ordered by `board_id` ascending
  (`board_01`, `board_02`, …).

## Each round row

| Field | Meaning |
| --- | --- |
| `board_id` | Round name matching the puzzle file stem. |
| `status` | `win`, `trap`, or `fort` under the rules below. |
| `winning_side` | `black` or `white`. |
| `coop_fillable` | Whether Black can still finish a north-south stone chain if White stops fighting. |
| `key_cells` | On `win`: Black first plays that keep the force. On `trap` / `fort`: `[]`. |
| `refutations` | On `trap`: one `{ "cell", "reply" }` per one-stone threat. On `win` / `fort`: `[]`. |

## How a round is scored

Every round is Black to move. Two independent questions decide the row:

1. **Can Black force a chain of stones from the north shore to the south shore against best White resistance?**
2. **Could Black still finish that shore-to-shore chain if White stopped contesting** — that is, if every remaining empty cell were eventually Black's?

### win

Black to move can force the north-south chain no matter how White answers. Set
`status` to `win`, `winning_side` to `black`, and `coop_fillable` to `true`.

Fill `key_cells` with the Black first plays that keep the force — every listed
cell must be a Black move that, played now, still leaves Black able to finish
the shore chain under best White defense. At least one such cell is required.
Leave `refutations` empty.

A first play that finishes the shore chain immediately makes the round a
`win`, but the interesting wins need several stones of forcing play before
the shores meet, so probing one cell with the judge is not enough to settle
a round.

### trap

Black cannot force the shore chain — White always has an answer that keeps
the north and south shores apart — yet the chain is still reachable under
cooperation (some north-south route avoids White's stones). Set `status` to
`trap`, `winning_side` to `white`, and `coop_fillable` to `true`. Leave
`key_cells` empty.

A surface reading that only asks "is a shore chain still fillable if White
passes" says yes on every trap. That reading is the sensei whisper, and it
is not the verdict: the round is still a `trap`, not a `win`, because White
fights.

#### Refutation coverage on a trap

A Black first play **threatens** when, after that play, Black would finish
the north-south chain on its very next single stone if White did nothing.
For every threatening first play, `refutations` must carry a White reply that
answers it: a legal White stone that, played right after the Black try,
leaves Black unable to close the shores on the following single stone.

Each row is `{"cell": "<the Black try>", "reply": "<the White answer>"}`.
Every threatening first play must appear (the required set must be a subset
of what you submit). Extra rows are allowed when they follow the same
threat-and-answer rule and keep the shores apart. A Black try that finishes
the chain outright is a finished chain, not a threat row — do not list it.
Two-or-more-stone hunts that only work while White keeps helping are not
threats.

### fort

Black cannot finish the shore chain even if White stopped contesting —
White's stones already wall the north and south shores apart (White already
holds an east-west blockade). Set `status` to `fort`, `winning_side` to
`white`, and `coop_fillable` to `false`. Leave both `key_cells` and
`refutations` empty.

## Tiny shape sample

```json
{
  "schema_tag": "hex-shore-v1",
  "rounds": [
    {"board_id": "board_01", "status": "win", "winning_side": "black",
     "coop_fillable": true, "key_cells": ["e2"], "refutations": []},
    {"board_id": "board_02", "status": "trap", "winning_side": "white",
     "coop_fillable": true, "key_cells": [],
     "refutations": [{"cell": "e1", "reply": "e2"}]},
    {"board_id": "board_03", "status": "fort", "winning_side": "white",
     "coop_fillable": false, "key_cells": [], "refutations": []}
  ]
}
```
