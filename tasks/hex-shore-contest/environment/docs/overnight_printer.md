# Overnight printer

`/app/kiosk/emit_card.sh` is the desk's overnight card printer. It reads the
round files, applies a quick in-house reading, and writes a draft card so the
morning desk has something on paper before the table opens.

The printer is a convenience, not the authority. It has repeatedly disagreed
with the sealed table judge — it leans on the sensei's surface fillability
whisper, so it tends to call fighting traps "wins", and it has mislabelled
which side really holds the board on the walled-off rounds. Its draft
ordering has also drifted between runs.

Treat the printer's output as a starting draft at most. The finished card at
`/output/hex-card.json` must reflect the table judge and the scoring rules in
`score_card.md`, not the printer's guesses. If you do lean on the
printer, a correct card must still come out the same on a second run.
