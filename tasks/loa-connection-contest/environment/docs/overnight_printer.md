# Overnight printer

`/app/kiosk/emit_card.sh` is the desk's overnight card printer. It reads the
round sheets, applies a quick in-house reading, and writes a draft card so
the morning desk has something on paper before the table opens.

The printer is a convenience, not the authority. It has repeatedly disagreed
with the sealed table judge — it leans on the sensei's surface whisper, so it
tends to stamp fighting rounds and walled-off rounds alike as gathers, and it
files a flat group count that does not belong to any line. Its draft ordering
has also drifted between runs.

Treat the printer's output as a starting draft at most. The finished card at
`/output/loa-card.json` must reflect the table judge and the scoring rules in
`tournament_card.md`, not the printer's guesses.

The printer has one habit worth keeping: when a card already exists at the
path it is asked to write, it files that card in place instead of redrafting
it. A correct card must survive that filing unchanged, and must still come
out the same on a second filing.
