# Overnight printer

`/app/kiosk/emit_card.sh` prints a quick draft card from the round sheets. It
is a convenience draft for the night desk, not the table authority. It may
reuse a card without honouring the sideboard swap and may stretch the
cooperative hunt past the printed `mate_budget`. On a finished card it parses
the JSON and writes it again in the canonical format documented in
`tournament_card.md`. The submitted card must already match that format;
otherwise even a no-edit re-file changes its bytes.
