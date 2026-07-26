# Score card

Hand in `/output/xiangqi-card.json`. Spellings are case-sensitive.

## Top level

- `schema_tag` must be exactly `xiangqi-mate-v1`.
- `rounds` lists every booklet board, ordered by `board_id` ascending
  (`board_01`, `board_02`, …).

## Each round row

| Field | Meaning |
| --- | --- |
| `board_id` | Round name matching the puzzle file stem. |
| `status` | `win`, `trap`, or `fort` under the rules below. |
| `mate_in` | On `win`: shortest forced mate length in **Red plies** (1–3). On `trap`: shortest cooperative mate length in Red plies. On `fort`: `0`. |
| `sequence` | On `win`: a forcing colour-prefixed ICCS line. On `trap` / `fort`: `[]`. |
| `river_cross` | Whether any step of the filed win `sequence` crosses the river. Otherwise `false`. |
| `refutations` | On `trap`: one `{ "move", "reply" }` per threatening Red first try. On `win` / `fort`: `[]`. |
| `coop_mate` | Whether Black can still be mated if both sides cooperate toward mating Black within three Red plies. |

## How a round is scored

Every round is Red to move. Two independent questions decide the row:

1. **Can Red force checkmate against best Black defense within three Red plies?**
2. **Could Black still be mated within three Red plies if both sides cooperated toward that mate?**

### win

Red to move can force mate no matter how Black answers, in at most three Red
plies. Set `status` to `win` and `coop_mate` to `true`. Set `mate_in` to the
**shortest** forced length in Red plies — padding a shorter mate with idle
checks or detours fails the card. Leave `refutations` empty.

Fill `sequence` with a forcing line as colour-prefixed ICCS moves
(`"red e5e9"`, `"black e9d9"`, …). Coordinates use files `a`–`i` and ranks
`0`–`9` (Red's back rank is `0`). The sealed judge must accept every step and
Black must be mated at the end. The line must itself be forcing: after every
Red ply, every legal Black reply must still leave Red able to finish within
the leftover Red-ply budget.

Set `river_cross` to `true` when any move in that sequence carries a piece
from one side of the river to the other (between ranks `4` and `5`); otherwise
`false`.

### trap

Red cannot force mate within three Red plies, yet a cooperative mate still
exists within three Red plies. Set `status` to `trap` and `coop_mate` to
`true`. Leave `sequence` empty. Set `mate_in` to the shortest cooperative
mate length.

A surface reading that only asks "would this horse leap mate if nothing
blocked it" or "can Black be mated if Black helps" can look cheerful on every
trap. That reading is the sensei whisper, and it is not the verdict: the round
is still a `trap`, not a `win`, because Black fights.

#### Refutation coverage on a trap

A Red first try **threatens** when, after that try, Red would mate on its very
next ply if Black did nothing — that is, there is a Red follow-up that mates
immediately from the post-try position treated as Red to move again. Immediate
mates on the first try are finished mates, not threat rows.

For every threatening first try, `refutations` must carry a Black reply that
answers it: a legal Black move that, played right after the Red try, leaves
Red unable to mate on the following single ply.

Each row is `{"move": "<the Red try in ICCS>", "reply": "<the Black answer>"}`.
Every threatening first try must appear (the required set must be a subset of
what you submit). Extra rows are allowed when they follow the same
threat-and-answer rule and keep Black unmated for one more Red ply.

### fort

Black cannot be mated even cooperatively within three Red plies. Set `status`
to `fort`, `coop_mate` to `false`, and `mate_in` to `0`. Leave `sequence` and
`refutations` empty. Set `river_cross` to `false`.

## Tiny shape sample

```json
{
  "schema_tag": "xiangqi-mate-v1",
  "rounds": [
    {"board_id": "board_01", "status": "win", "mate_in": 1, "sequence": ["red e5e9"],
     "river_cross": false, "refutations": [], "coop_mate": true},
    {"board_id": "board_02", "status": "trap", "mate_in": 2, "sequence": [],
     "river_cross": false,
     "refutations": [{"move": "a5e5", "reply": "e9d9"}], "coop_mate": true},
    {"board_id": "board_03", "status": "fort", "mate_in": 0, "sequence": [],
     "river_cross": false, "refutations": [], "coop_mate": false}
  ]
}
```
