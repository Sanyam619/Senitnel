A day-ahead commitment batch under `/opt/distro` ingests board feeds from `/data/fixtures` and writes `/data/out/answers.json` (`version` = `1` plus exactly twelve `rounds`). Runs use `/opt/distro/scripts/run-cycle.sh`.

The pipeline currently emits incorrect commitment results across the twelve boards. Repair the batch under `/opt/distro` so each board's cleared units, settlement token (`smp`), reserve binding, status, and clause refutation match the house rules under `/opt/distro/config/`. Leave `/data/fixtures` and `/opt/distro/lib/rowcheck.jar` unchanged — the sealed row checker rejects illegal answer rows.

Staging drafts under `/data/staging/` often disagree with the checker.
