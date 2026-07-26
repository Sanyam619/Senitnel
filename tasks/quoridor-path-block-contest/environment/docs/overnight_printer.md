# Overnight printer

`/app/kiosk/emit_card.sh` is the desk's overnight card printer. It reads the
rounds, applies the sensei whisper, and writes a draft under
`/output/quoridor-card.json`. It is a convenience draft for the desk, not
the authority for the tournament card.

On several rounds the draft has disagreed with a careful reading against
the sealed table judge — especially where a corridor looks blocked at a
glance but White still has a fighting answer. Prefer the score-card rules
and the judge's legality/path outputs over the overnight draft.

If `/output/quoridor-card.json` already holds a completed card with the
booklet schema and every round present, filing again must leave the bytes
unchanged.
