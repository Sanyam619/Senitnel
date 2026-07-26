# Overnight printer

`/app/kiosk/emit_card.sh` is the desk's overnight card printer. It reads
the rounds, applies the sensei whisper, and writes a draft under
`/output/hive-card.json`. It is a convenience draft for the desk, not the
authority for the tournament card.

On several rounds the draft has disagreed with a careful reading against
the sealed table judge — especially where one White piece looks able to
step straight onto the last open queen-neighbor at a glance, but that step
is not actually legal once one-hive continuity and gate rules are checked,
or where Black still has a fighting answer.

If `/output/hive-card.json` already holds a completed card with the
booklet schema and every round present, filing again must leave the bytes
unchanged.
