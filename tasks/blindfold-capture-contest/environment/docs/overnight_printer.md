# Overnight printer notes

Draft card scripts live under `/app/kiosk/`. Recent overnight runs disagreed with the sealed table judge.

What people saw on the floor:

1. **Announce tags** — match logs under `/app/history/` show how the table spoke on accepted captures. Some printer drafts filed a different capture tag shape. The judge rejected those lines.

2. **Trap rounds** — `/app/tools/sensei_hint.sh` marked several rounds `looks_fillable_if_defender_passes`. Drafts stamped those as forced wins. White replies left the marked piece on the board. A White-pass fill is not a win.

3. **Reply certificates** — For cooperatively capturable unwinnable rounds, the card needs White replies for Black first-tries that capture on the next move after White passes (see the tournament card notes). Longer printer hunts are not that list.

The sealed judge remains `/app/bin/judge.jar`. Draft kiosk scripts are not authoritative for the card.
