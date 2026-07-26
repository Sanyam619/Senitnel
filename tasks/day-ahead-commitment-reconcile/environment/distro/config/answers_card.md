# Answers card

`/data/out/answers.json` carries `version` `1` and twelve `rounds` ordered as `board_01` … `board_12`.

Each round: `round_id`, `cleared` (`unit_id`, `mw`, `offer_price`), `smp`, `reserve_binds`, `status` (`feasible_clear` | `infeasible` | `reserve_short`), and `refutation` on blocked statuses only.

Emit with `/opt/distro/scripts/run-cycle.sh` after `/opt/distro` is correct. Two writes of the same settled file stay byte-identical.
