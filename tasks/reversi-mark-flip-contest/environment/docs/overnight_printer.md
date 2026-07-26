# Overnight kiosk drafts

The kiosk under `/app/kiosk/` prints a draft card overnight so the desk has
something to read at breakfast. It plays Black alone: it hunts for any line that
turns the mark while White sits still, allows itself a fourth stone when three
will not do, and stamps `win` whenever it finds one. It never asks what White
would have replied, and it never fills in refutations.

Tables have thrown out that draft more than once. Treat `/app/kiosk/draft_card.json`
as breakfast reading: the verdict words, the stone budget, and the refutation
rows all have to come from real play against a fighting White.
