# Filing the tournament card

File one card at `/output/patchwork-card.json` covering every round under
`/app/puzzles/`. The rules of play live in `contest_rules.md`; the sheet layout
in `board_format.md`; the referee dialect in `table_judge.md`.

The card is a JSON object:

- `schema_tag` — a short string tag for the card.
- `rounds` — one object per round, each with:
  - `board_id` — the sheet id.
  - `status` — `win`, `trap`, or `fort` (see `contest_rules.md`).
  - `patch_id` — the first patch Red takes in the filed line; empty on a fort.
  - `time_cost` — the time cost of that opening patch (its own printed time);
    zero on a fort.
  - `buttons` — the printed income of that opening patch; zero on a fort.
  - `sequence` — the filed line of turns, in the move dialect, interleaving Red
    and Blue turns in the order the table would play them. Empty on a fort.
  - `refutations` — a list of `{patch_id, reply}` objects; used only on trap
    rounds, empty otherwise.
  - `coop_fill` — whether the floor is reachable against a Blue that only
    advances (true on win and trap rounds, false on a fort).

## What each verdict must carry

- **win** — a `sequence` whose every Red turn keeps the floor forced against all
  Blue answers, ending with both tokens at the end of the track and Red at or
  above the floor. No refutations.
- **trap** — a `sequence` that reaches the floor while Blue only advances, plus a
  `refutations` entry for **every** takeable opening: each entry names an opening
  `patch_id` Red could take first and a Blue `reply` (`advance` or `take PX`)
  that holds Red under the floor afterward.
- **fort** — empty `sequence`, empty `refutations`, empty `patch_id`.

Every filed line is replayed past the sealed judge, and every verdict is
recomputed from the sheet, so a status that does not survive real play — or a
line that does not reach the floor — does not score.
