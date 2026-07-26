# Score card

Hand in `/output/c4-card.json`. Spellings are case-sensitive.

## Top level

- `schema_tag` must be exactly `c4-zugzwang-v1`.
- `rounds` lists every booklet board, ordered by `board_id` ascending
  (`01`, `02`, …).

## Each round row

| Field | Meaning |
| --- | --- |
| `board_id` | Round id as printed on the sheet (`01` … `12`). |
| `status` | `win`, `trap`, or `draw` under `contest_rules.md`. |
| `best_column` | On `win` / `trap`: the first Yellow column of the filed sequence. On `draw`: `-1`. |
| `win_in` | Count of Yellow drops in the filed sequence (0 on `draw`). |
| `sequence` | Colour-tagged drops that witness the verdict. |
| `threats` | On `trap` / `draw`: `{column, row}` gravity landings for graded threats / context. On `win`: `[]`. |
| `refutations` | On `trap` / `draw`: coverage rows. On `win`: `[]`. |
| `coop_win` | Whether the friendly five-drop climb exists. |

## What the sequence shows

| verdict | sequence |
| --- | --- |
| `win` | Forcing line: Yellow and Red drops in play order, ending when Yellow connects four. Each of Yellow's drops in it must still force the connect with the drops left — a line that only works because Red answered softly is refused. |
| `trap` | Friendly line: Yellow drops only, at most five, Red sitting still, ending when Yellow connects. Any friendly line that gets there is accepted. |
| `draw` | Empty. |

On a `win`, `best_column` must be a forcing first drop (still forces with five
drops of budget). On a `trap`, `best_column` is simply the first drop of the
friendly sequence. Do not pad `win_in` past the drop that completes four — the
sealed judge refuses extra dangling drops after a connect.

## Tiny shape sample

Shape only — the rounds below are from an old booklet, not the one on the desk:

```json
{
  "schema_tag": "c4-zugzwang-v1",
  "rounds": [
    {
      "board_id": "41",
      "status": "win",
      "best_column": 3,
      "win_in": 2,
      "sequence": ["yellow 3", "red 1", "yellow 3"],
      "threats": [],
      "refutations": [],
      "coop_win": true
    },
    {
      "board_id": "42",
      "status": "trap",
      "best_column": 2,
      "win_in": 2,
      "sequence": ["yellow 2", "yellow 2"],
      "threats": [{"column": 2, "row": 3}],
      "refutations": [{"column": 2, "reply": 4}],
      "coop_win": true
    },
    {
      "board_id": "43",
      "status": "draw",
      "best_column": -1,
      "win_in": 0,
      "sequence": [],
      "threats": [],
      "refutations": [{"column": 0, "reply": 3}],
      "coop_win": false
    }
  ]
}
```
