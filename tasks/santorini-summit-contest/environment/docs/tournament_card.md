# Tournament card

File the card at `/app/answers.json`:

Shape only — the rounds below are from an old booklet, not the one on the desk:

```json
{
  "rounds": [
    {
      "board_id": "board_41",
      "status": "win",
      "coop_summit": true,
      "key_move": "F:b2-c3",
      "sequence": ["F:b2-c3"],
      "refutations": []
    },
    {
      "board_id": "board_42",
      "status": "trap",
      "coop_summit": true,
      "key_move": "",
      "sequence": [],
      "refutations": [{"move": "F:a2-b3:c3", "reply": "S:d4-c4:c5"}]
    },
    {
      "board_id": "board_43",
      "status": "fort",
      "coop_summit": false,
      "key_move": "",
      "sequence": [],
      "refutations": []
    }
  ]
}
```

- One row per sheet under `/app/puzzles/`, `board_id` spelled as printed there.
- `status` is one of the three verdict words in `contest_rules.md`.
- Move tokens follow the dialect in `table_judge.md` and the match logs.

## What each verdict means

Every round is First to move. First spends turns from the sheet's `budget`.
Second answers when the fight matters.

| verdict | what to file |
| --- | --- |
| `win` | First forces a level-3 summit against every Second answer. Set `coop_summit` true. Fill `key_move` with one forcing first-move token and `sequence` with one forcing line (First, Second, First, …). Leave `refutations` empty. |
| `trap` | First cannot force the summit, yet a First-only plan still summits if Second never moves. Set `coop_summit` true. Leave `key_move` and `sequence` empty. Fill `refutations` for every threat (below). |
| `fort` | Even with Second passing, no legal First plan of length ≤ `budget` summits. Set `coop_summit` false. Leave `key_move`, `sequence`, and `refutations` empty. |

A surface reading that ignores dome blocks often says the peak is open on every
trap. That reading is the sensei whisper, and it is not the verdict.

## Threat moves and refutation coverage

A First first turn **threatens** when:

1. that turn alone does **not** summit, and
2. there exists a second legal First turn such that, with Second still on
   the same layout (Second passed), the first turn then the second summits
   onto level 3.

For every threatening first turn, `refutations` must carry a Second reply
that answers it: a legal Second move+build (or ascent token) such that after
First plays the threat and Second answers, **no** single First follow-up
summits.

Each row is `{"move": "<move token>", "reply": "<move token>"}`. Every
required threat must appear (required ⊆ submitted). Extra rows are allowed
when they follow the same threat-and-answer rule. A first turn that alone
summits is a finished ascent, not a threat row.

The table checks the whole booklet at once, so a round filed on a hunch costs
that round.
