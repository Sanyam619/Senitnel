# Tournament card

File the card at `/output/jaipur-card.json`. One row per sheet under
`/app/puzzles/`, `board_id` spelled as printed there, rows ordered by
`board_id` ascending. `schema_tag` is `jaipur-trade-v1`.

Shape only — the rounds below are from an old booklet, not the one on the desk:

```json
{
  "schema_tag": "jaipur-trade-v1",
  "rounds": [
    {
      "board_id": "41",
      "status": "win",
      "action": "sell:clo:3",
      "tokens": ["clo:5", "clo:3", "clo:2", "b3:2"],
      "score": 12,
      "sequence": ["trader sell:clo:3"],
      "refutations": [],
      "coop_seal": true
    },
    {
      "board_id": "42",
      "status": "trap",
      "action": "sell:lea:2",
      "tokens": ["lea:4", "lea:3", "spi:5"],
      "score": 12,
      "sequence": ["trader sell:lea:2", "trader sell:spi:1"],
      "refutations": [{"action": "sell:lea:2", "reply": "sell:spi:1"}],
      "coop_seal": true
    },
    {
      "board_id": "43",
      "status": "fort",
      "action": "",
      "tokens": [],
      "score": 0,
      "sequence": [],
      "refutations": [],
      "coop_seal": false
    }
  ]
}
```

- `status` is one of the three verdict words in `contest_rules.md`.
- `action` is the first Trader action on a `win` or `trap` line, and `""` on a
  `fort`.
- `tokens` lists the goods-token and bonus labels the sealed judge reports for
  the filed line (`[]` on a `fort`); padding extra claims is refused.
- `score` is the Trader score the sealed judge reports after replaying the
  filed line (`0` on a `fort`); padding above that count is refused.
- `sequence` carries the colour-tagged turns that witness the verdict — a
  fighting line on a `win`, a friendly Trader-only line on a `trap`, empty on a
  `fort`.
- `refutations` covers the sheet's seal-losing first-sell threats on a `trap`
  (see `contest_rules.md`), and is empty on a `win` or `fort`. Each row uses
  `action` and `reply`.
- `coop_seal` says whether the friendly climb exists inside three Trader
  actions (so `win` and `trap` carry `true`, `fort` carries `false`).

The table checks the whole booklet at once, so a round filed on a hunch costs
that round. A finished card already at `/output/jaipur-card.json` stays
byte-identical when the desk emits it twice with no edits.
