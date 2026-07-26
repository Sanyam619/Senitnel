# Score card

Hand in `/output/blokus-card.json`. Spellings are case-sensitive.

## Top level

- `schema_tag` must be exactly `blokus-corner-v1`.
- `rounds` lists every booklet board, ordered by `board_id` ascending
  (`01`, `02`, …).

## Each round row

| Field | Meaning |
| --- | --- |
| `board_id` | Round id as printed on the sheet (`01` … `10`). |
| `status` | `win`, `trap`, or `fort` under `contest_rules.md`. |
| `piece_id` | On `win` / `trap`: piece id of the first Blue placement. On `fort`: `""`. |
| `placement` | On `win` / `trap`: squares string of that first placement (`b2,b3,c3`). On `fort`: `""`. |
| `squares_left` | Blue inventory square count after the filed sequence (0 on a successful fill; on `fort` the opening count). |
| `sequence` | Colour-tagged placements that witness the verdict. |
| `refutations` | On `trap`: threat coverage rows. On `win` / `fort`: `[]`. |
| `coop_fill` | Whether the friendly three-placement climb exists. |

## What the sequence shows

| verdict | sequence |
| --- | --- |
| `win` | Forcing line: Blue and Yellow placements in play order, ending when the squares-left floor is met. Each of Blue's placements in it must still force the floor with the placements left — a line that only works because Yellow answered softly is refused. |
| `trap` | Friendly line: Blue placements only, at most three, Yellow sitting still, ending when the floor is met. Any friendly line that gets there is accepted. |
| `fort` | Empty. |

On a `win`, the opening `piece_id`/`placement` must be a forcing first try
(still forces with three placements of budget). On a `trap`, they are simply
the first step of the friendly sequence. Do not pad `squares_left` away from
what the sealed judge reports after replaying the sequence.

## Tiny shape sample

Shape only — the rounds below are from an old booklet, not the one on the desk:

```json
{
  "schema_tag": "blokus-corner-v1",
  "rounds": [
    {
      "board_id": "41",
      "status": "win",
      "piece_id": "V3",
      "placement": "b2,b3,c3",
      "squares_left": 0,
      "sequence": ["blue V3@b2,b3,c3", "yellow 2@d1,e1", "blue 1@c1"],
      "refutations": [],
      "coop_fill": true
    },
    {
      "board_id": "42",
      "status": "trap",
      "piece_id": "I3",
      "placement": "a2,a3,a4",
      "squares_left": 0,
      "sequence": ["blue I3@a2,a3,a4", "blue 1@b5"],
      "refutations": [{"piece_id": "V3", "reply": "2@c1,d1"}],
      "coop_fill": true
    },
    {
      "board_id": "43",
      "status": "fort",
      "piece_id": "",
      "placement": "",
      "squares_left": 4,
      "sequence": [],
      "refutations": [],
      "coop_fill": false
    }
  ]
}
```
