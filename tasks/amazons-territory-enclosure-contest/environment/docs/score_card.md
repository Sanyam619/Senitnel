# Score card

Hand in `/output/amazons-card.json`. Spellings are case-sensitive.

## Top level

- `schema_tag` must be exactly `amazons-territory-v1`.
- `rounds` lists every booklet board, ordered by `board_id` ascending
  (`01`, `02`, …).

## Each round row

| Field | Meaning |
| --- | --- |
| `board_id` | Round id as printed on the sheet (`01` … `11`). |
| `status` | `win`, `trap`, or `fort` under `contest_rules.md`. |
| `best_move` | On `win` / `trap`: the first White turn of the filed sequence (`a4-b3/c2`). On `fort`: `""`. |
| `territory_delta` | Exclusive White-minus-Black delta after the filed sequence (0 on `fort`). |
| `sequence` | Colour-tagged turns that witness the verdict. |
| `refutations` | On `trap`: threat coverage rows. On `win` / `fort`: `[]`. |
| `coop_enclose` | Whether the friendly three-turn climb exists. |

## What the sequence shows

| verdict | sequence |
| --- | --- |
| `win` | Forcing line: White and Black turns in play order, ending when the territory floor is met. Each of White's turns in it must still force the floor with the turns left — a line that only works because Black answered softly is refused. |
| `trap` | Friendly line: White turns only, at most three, Black sitting still, ending when the floor is met. Any friendly line that gets there is accepted. |
| `fort` | Empty. |

On a `win`, `best_move` must be a forcing first turn (still forces with three
turns of budget). On a `trap`, `best_move` is simply the first turn of the
friendly sequence. Do not pad `territory_delta` above what the sealed judge
reports after replaying the sequence.

## Tiny shape sample

Shape only — the rounds below are from an old booklet, not the one on the desk:

```json
{
  "schema_tag": "amazons-territory-v1",
  "rounds": [
    {
      "board_id": "41",
      "status": "win",
      "best_move": "a4-b3/c2",
      "territory_delta": 3,
      "sequence": ["white a4-b3/c2", "black e1-e2/d2", "white b3-c3/b3"],
      "refutations": [],
      "coop_enclose": true
    },
    {
      "board_id": "42",
      "status": "trap",
      "best_move": "e1-e2/e1",
      "territory_delta": 2,
      "sequence": ["white e1-e2/e1", "white e2-d3/c2"],
      "refutations": [{"move": "e1-e2/c4", "reply": "a1-a2/b3"}],
      "coop_enclose": true
    },
    {
      "board_id": "43",
      "status": "fort",
      "best_move": "",
      "territory_delta": 0,
      "sequence": [],
      "refutations": [],
      "coop_enclose": false
    }
  ]
}
```
