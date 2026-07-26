# Tournament card

Hand in your finished card at `/app/answers.json`. Names and spellings are case-sensitive.

## What the card must say

Name the ko rule this table is using (`rule`). Pick exactly one of:

- `positional_superko`
- `situational_superko`
- `natural_situational_superko`

Then list all twelve rounds under `boards`, ordered by `board_id` from 1 to 12.

## How a round is judged

For every round, answer two separate questions:

1. **Can Black force the capture when White fights to keep the target alive?** That is `status`. White answers whenever a useful reply exists. A capture that only works because White keeps passing is not a win.
2. **If White always passes, can Black still empty the target?** That is `coop_capturable`.

Some open-eye shapes fill when White cooperates and still count as unwinnable when White resists. A sensei whisper that only counts liberties can look cheerful on those shapes.

On a winning line, White may pass only when White has no useful liberty play left. Passing while the target still has two or more liberties and at least one of those points is a legal White stone is cooperative and is rejected.

## Each round row

Every row carries `board_id`, `status`, and `coop_capturable`.

### Wins

Add `sequence`: the forcing line as colour-prefixed moves (`"black R,C"`, `"white R,C"`, `"black pass"`, `"white pass"`). Coordinates are 1-indexed on the 9×9 goban.

The table judge must accept every move and the target must be empty at the end. The line must include at least one White stone play. Black stone plays (`"black R,C"` only) must meet these floors:

| round | Black stones |
| ---: | ---: |
| 1 | 6 |
| 2 | 6 |
| 3 | 5 |
| 4 | 5 |

### Unwinnable rounds

Skip `sequence`.

- If `coop_capturable` is false, skip `refutations` too (or leave them empty).
- If `coop_capturable` is true, add `refutations`: one White reply for each empty liberty of the target on the **starting** goban. Each reply looks like `{"after_black": "R,C", "white": "R,C"}` or `{"after_black": "R,C", "white": "pass"}`.

Every starting liberty appears once. For each pair, the two-move try `black …` then the listed White reply must be legal for the judge and must leave the target still occupied.

## Tiny shape sample

```json
{
  "rule": "situational_superko",
  "boards": [
    {"board_id": 1, "status": "win", "coop_capturable": true, "sequence": ["black 1,1", "white 1,2", "black 2,1"]},
    {"board_id": 2, "status": "unwinnable", "coop_capturable": true, "refutations": [{"after_black": "3,3", "white": "3,4"}]},
    {"board_id": 3, "status": "unwinnable", "coop_capturable": false}
  ]
}
```
