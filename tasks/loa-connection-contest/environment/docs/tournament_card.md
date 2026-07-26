# Tournament card

Hand in the finished card at `/output/loa-card.json`. Names and spellings
are case-sensitive.

## What the card must say

Keep `schema_tag` as `loa-connection-v1`. List every contest round under
`rounds`, ordered by `board_id` ascending (`board_01` … `board_12`).

| Field | Meaning |
| --- | --- |
| `board_id` | Round name matching the puzzle sheet stem. |
| `status` | `win`, `trap`, or `fort` under the readings below. |
| `key_move` | On `win`: one forcing first move token. On `trap` / `fort`: `""`. |
| `components` | Black's group count as scored for that verdict — see `component_floors.md`. |
| `sequence` | On `win`: move tokens for one forcing line. On `trap` / `fort`: `[]`. |
| `refutations` | On `trap`: `{ "move", "reply" }` coverage for every threatening first move. On `win` / `fort`: `[]`. |
| `coop_connect` | Whether Black could still gather into one group if White stopped moving. |

## How a round is judged

Every round is Black to move. Two questions decide the row:

1. **Can Black force one connected group inside two Black moves while White
   answers?**
2. **Could Black still gather into one group with a short run of Black moves
   if White never moved again?**

Both readings run to the lengths set out in `contest_rules.md`. Those lengths
are the contest's, not a hint about how to search: a round that only falls to
a longer fight is not a gather here, and a round that only opens up to a
longer cooperative hunt is not reachable here.

### win

Black gathers on this very move, or Black has a first move after which
**every** legal White answer still leaves at least one legal Black move that
gathers. If some White answer leaves Black with no gathering move, that
first move is not forcing. If White has no legal answer at all, Black must
still have a gathering move on the turn that follows.

Set `status` to `win` and `coop_connect` to `true`. Put one forcing first
move in `key_move`. Fill `sequence` with one legal line that starts with
that same move; the steps alternate sides, Black first, so a round that
needs two Black turns carries a legal White answer in between. Leave
`refutations` empty.

Some rounds gather in a single move. The interesting ones do not, and
probing one move with the judge is not enough to settle a round.

### trap

Black cannot force the gather inside its two moves — White always has an
answer that keeps Black split — yet a Black-only run inside the cooperative
length still gathers if White stops playing. Set `status` to `trap` and
`coop_connect` to `true`. Leave `key_move` empty and `sequence` empty.

A surface reading that lets pieces travel any distance and ignores enemy
pieces in the way says the round looks ready on every trap. That reading is
the sensei whisper, and it is not the verdict: the round is still a `trap`,
not a `win`, because White fights.

#### Threats and refutation coverage

A Black first move **threatens** when:

1. that move alone does **not** gather Black into one group, and
2. with White still standing still, some second Black move would gather.

For every threatening first move, `refutations` must carry a White reply
that answers it: a legal White move played right after the Black try, after
which no single Black move gathers.

Each row is `{"move": "<the Black try>", "reply": "<the White answer>"}`.
Every threatening first move must appear — the required set has to be a
subset of what you submit. Extra rows are allowed when they follow the same
threat-and-answer rule. A Black try that gathers outright is a finished
round, not a threat row, so do not list it.

### fort

Even with White standing still, no Black-only run inside the cooperative
length gathers Black into one group — White's pieces wall the Black groups
apart for longer than the run lasts. Set `status` to `fort` and
`coop_connect` to `false`. Leave `key_move`, `sequence`, and `refutations`
empty.

A walled-off round can still look forcible to a hunt that fights on past
Black's two moves, because a White answer has to move something. That does
not make it a gather, and it does not make it reachable while White stands
still.

## Shape sample

The rows below come from three scratch positions the desk keeps for
newcomers, not from this booklet. They show the shape only.

```json
{
  "schema_tag": "loa-connection-v1",
  "rounds": [
    {"board_id": "board_97", "status": "win", "key_move": "b2-b4",
     "components": 1, "sequence": ["b2-b4", "e5-e3", "d1-d3"],
     "refutations": [], "coop_connect": true},
    {"board_id": "board_98", "status": "trap", "key_move": "",
     "components": 1, "sequence": [],
     "refutations": [{"move": "f6-f4", "reply": "c1-c3"}],
     "coop_connect": true},
    {"board_id": "board_99", "status": "fort", "key_move": "",
     "components": 4, "sequence": [], "refutations": [],
     "coop_connect": false}
  ]
}
```

Read every contest round off the sheets and the table judge. Nothing above
is a verdict for `board_01` … `board_12`.
