# Overnight printer notes

Staff found the overnight printer sources under `/app/kiosk/`. Drafts from `python -m kiosk doctor` and `python -m kiosk emit` recently diverged from the sealed table judge. A finished card that was typed by hand while those commands still disagree with the table does not clear the floor — grading re-runs doctor/emit against the live sources.

What people saw on the floor:

1. **Ko family** — The printer's guess from `/app/history/` did not match the judge's refusal pattern on the same books. Same-colour cites and other-colour cites were argued about as if they carried the same weight. Doctor prints a line `printer_ko_guess=...` that must match the live table family.

2. **Trap rounds** — Sensei whispers marked several rounds `looks_fillable_if_white_passes`. The printer stamped those as forced wins. White liberty answers left the target occupied. A White-pass fill is not the same stamp as a forced win. Doctor samples round 5 as `printer_round_5={...}`.

3. **Reply certificates** — For rounds that only fall under White pass, the printer filed reply lists that were all passes. The table rejected those whenever a liberty stone reply still kept the target alive. A fresh `python -m kiosk emit -o /tmp/card.json` must file stone replies on those trap rounds.

The sealed judge remains `/app/bin/judge.jar`.
