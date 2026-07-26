# Reviewer note — quoridor-path-block-contest

## Version 2 GO

Games-category Quoridor path-block tournament booklet. Agent files
`/output/quoridor-card.json` for 11 Black-to-move wall puzzles. Sealed
`judge.jar`, sensei corridor bait, kiosk draft bait. `languages=["bash"]`.

## What to verify

- Status mix: ≥3 win, ≥5 trap, ≥2 fort (shipped 4/5/2).
- Sensei marks every trap `looks_blocked` while the card files them as trap.
- Win sequences validate through the sealed judge; `path_len` equals true
  White shortest path (≥7); `key_wall` is a forcing first wall.
- Trap refutations cover required threat walls (⊆); replies kill second-wall
  coop completions.
- Forts cannot reach PATH_FLOOR=7 even with White passing.
- Judge and puzzles compared to `/opt/tbench` seals; no adjacent sha256.
- Oracle derives via search packages (`op_a`/`op_b`/`op_c`), not a hardcoded
  answer table.

## Construction manifest pointers

See `specs/quoridor-path-block-contest.md` for symbol_table,
flipping_point_contract, decoys, and code_forbidden_tokens.
