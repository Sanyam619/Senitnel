# Tournament card

Hand in the finished card at `/app/answers.json`. Names and spellings are
case-sensitive.

## What the card must say

Keep `schema_tag` as `onitama-temple-v1`. List every contest round under
`rounds`, ordered by `board_id` ascending (`01` … `12`).

The kiosk re-files a finished card before comparing its bytes. Write the
complete JSON object with Python's
`json.dumps(card, indent=2, sort_keys=True) + "\n"` form: two-space
indentation, keys sorted at every object level, and one trailing newline.
The first filed card must already use that form for a no-edit kiosk re-file
to remain byte-identical.

## How a round is judged

Every round is Sensei to move. Two questions decide the row:

1. **Can Sensei force a temple finish or master capture against fighting Pupil
   inside the sheet's `mate_budget`?**
2. **If Pupil never moves, can Sensei still finish inside that budget while
   cards keep rotating on Sensei's turns?**

### win

Sensei can force the finish no matter how Pupil answers. Set `status` to `win`
and `coop_temple` to `true`. Fill `sequence` with alternating Sensei and Pupil
plies that end when Sensei temples or captures the Pupil master. Each Sensei
ply in that line must still force the finish with the plies left. A line that
only works because Pupil answered softly is refused. Set `card_used` to the
card named in the first Sensei token, `mate_in` to the Sensei ply count, and
`sideboard` to the sideboard card after each ply. Leave `refutations` empty.

### trap

Pupil can hold the fight off under adversarial play, yet a Sensei-only finish
still works if Pupil sits still. Set `status` to `trap` and `coop_temple` to
`true`. Fill `sequence` with Sensei plies only (at most `mate_budget`), ending
when Sensei temples or captures. Any friendly line that gets there is accepted.
Set `card_used`, `mate_in`, and `sideboard` the same way as on a win.

A surface reading that ignores the sideboard swap often cheers every trap as
ready. That reading is the sensei whisper, and it is not the verdict: the round
is still a `trap`, not a `win`, because Pupil fights.

#### Threat moves and refutation coverage

A Sensei first card **threatens** when it does not finish immediately, but after
that ply (with Pupil sitting still) Sensei can still finish inside the remaining
budget. Each such first card needs a Pupil `reply` after which that remaining
cooperative finish is gone. Coverage is required ⊆ submitted: every graded
threat must appear as a `card` with a working `reply`. Extra correct rows are
allowed.

### fort

Even with Pupil sitting still, no Sensei finish fits inside `mate_budget`. Set
`status` to `fort` and `coop_temple` to `false`. Leave `card_used` empty,
`mate_in` at `0`, and `sequence`, `sideboard`, and `refutations` empty.

Do not pad `mate_in` past the Sensei ply that finishes. The sealed judge refuses
extra dangling plies after a finish when replaying with `--coop` on traps or
plain validate on wins.

## Tiny shape sample

Shape only. The rounds below are from an old booklet, not the one on the desk:

```json
{
  "schema_tag": "onitama-temple-v1",
  "rounds": [
    {
      "board_id": "41",
      "status": "win",
      "card_used": "Tiger",
      "mate_in": 2,
      "sequence": ["sensei Tiger:c2-c4", "pupil Frog:a5-b4", "sensei Crab:c4-c5"],
      "sideboard": ["Tiger", "Frog", "Crab"],
      "refutations": [],
      "coop_temple": true
    },
    {
      "board_id": "42",
      "status": "trap",
      "card_used": "Ox",
      "mate_in": 2,
      "sequence": ["sensei Ox:c2-c3", "sensei Crane:c3-c5"],
      "sideboard": ["Ox", "Crane"],
      "refutations": [{"card": "sensei Ox:c2-c3", "reply": "pupil Crab:a4-c4"}],
      "coop_temple": true
    },
    {
      "board_id": "43",
      "status": "fort",
      "card_used": "",
      "mate_in": 0,
      "sequence": [],
      "sideboard": [],
      "refutations": [],
      "coop_temple": false
    }
  ]
}
```
