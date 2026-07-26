# Tournament card

File the card at `/app/answers.json`:

Shape only — the rounds below are from an old booklet, not the one on the desk:

```json
{
  "rounds": [
    {
      "board_id": "41",
      "status": "win",
      "line": ["black f6|flips:2", "white g7|flips:1", "black e7|flips:3",
               "white h6|flips:1", "black g4|flips:4"],
      "refutations": []
    },
    {
      "board_id": "42",
      "status": "trap",
      "line": ["black c6|flips:1", "black d7|flips:2", "black e6|flips:3"],
      "refutations": [
        {"threat": "c6", "reply": "b7"},
        {"threat": "d7", "reply": "d8"}
      ]
    },
    {
      "board_id": "43",
      "status": "fort",
      "line": [],
      "refutations": []
    }
  ]
}
```

- One row per sheet under `/app/puzzles/`, `board_id` spelled as printed there.
- `status` is one of the three verdict words in `contest_rules.md`.
- Every drop in a `line` carries the house announce after `|`
  (see `announce_customs.md`), and Black plays the first drop.

## What the line shows

| verdict | line |
| --- | --- |
| `win` | The forcing line: Black's drops and White's replies in play order, ending on the Black drop that turns the mark. Each of Black's drops in it must still force the take with the stones left — a line that only works because White answered softly is refused. Write `white pass` for a turn where White has no legal drop. |
| `trap` | The friendly line: Black's drops only, at most three, White passing throughout, ending on the drop that turns the mark. Any friendly line that gets there is accepted. |
| `fort` | Empty. |

## Refutations

Only `trap` rounds carry refutations: one row per threat on the sheet, in any
order, `{"threat": "<square>", "reply": "<square>"}`. `win` and `fort` rounds
carry an empty list.

The table checks the whole booklet at once, so a round filed on a hunch costs
that round.
