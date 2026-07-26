# Patchwork time-track economy contest

Write `/output/patchwork-card.json` covering ten First-player (Red) rounds. Each
round hands you a quilt, an ordered patch market, a shared time track, and a
button/time floor Red is trying to reach. For every round decide whether Red can
**force** the floor against a Blue that spends tempo to stop it, whether the
floor is only reachable when Blue plays along, or whether it is out of reach even
then — and, on the rounds Blue can refuse, name the reply that answers each
tempo-losing opening.

Each round entry carries: `board_id`, `status`, the opening patch Red takes
(`patch_id`) with that patch's own `time_cost` and `buttons`, the full move
`sequence`, the `refutations` (each a `patch_id` with Blue's `reply`), and
`coop_fill`. The verdict words (`win`, `trap`, `fort`), the time-track "furthest
back moves next" rule, button income, overlap-free patch placement, the floor,
what counts as a refuted opening, and the move dialect the table replays are all
documented under `/app/docs/`. The card also carries a top-level `schema_tag`.

An overnight kiosk printed a draft card the table has thrown out, and the sensei
whisper only checks whether a patch geometrically fits — it is blind to the time
track and to buttons. Match logs under `/app/history/` show the dialect the table
expects for called moves.

Rounds: `/app/puzzles/`. Kiosk draft: `/app/kiosk/draft_card.json` (regenerate
with `/app/kiosk/emit_card.sh`). Whisper: `/app/tools/sensei_hint.sh`. Sealed
judge: `/app/bin/judge.jar`. Leave the sealed judge and the round sheets
unchanged.
