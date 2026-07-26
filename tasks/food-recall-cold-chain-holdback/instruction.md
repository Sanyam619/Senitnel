A grocery holdback batch ingests notice, probe, dock, review, and signoff feeds from `/data/fixtures` and writes `/data/out/<day>/holdback_ledger.jsonl`, `/data/out/<day>/release_auth_audit.json`, and `/data/out/<day>/affected_units.tsv`. Runs use `/opt/distro/scripts/run-cycle.sh` with `--day <distribution-day>` and `--root /data/fixtures`.

The pipeline currently emits incorrect holdback results. Distribution days `day_r0412` through `day_r0416` each expose a distinct defect; repair every day and leave `/data/fixtures` unchanged.

**Active recall vs signoff (r0412).** Broken: recalled dairy lots appear releasable at stores with a signoff grant. Fixed: active recall units remain on hold with a notice-active reason; unrelated units on the same day may release.

**Clean probe release (r0413).** Broken: frozen lots with valid probe readings and signoff grant stay on hold. Fixed: release with an OK-release reason.

**Cleared excursion (r0414).** Broken: QA-cleared excursions with signoff grant stay locked. Fixed: release with an OK-release reason.

**Dock split lineage (r0415).** Broken: one dock-split child keeps shipping on a flagged parent lot. Fixed: every split child stays on hold; a second run on the same day must not duplicate affected-unit rows (byte-stable ledger, audit, and TSV).

**Cross-store recall (r0416).** Broken: a multi-store recalled unit does not block all stores consistently. Fixed: unit on hold with notice-active reason; each affected store appears in the extract with matching exposure class and case counts.

Repair the batch pipeline under `/opt/distro`. Source edits take effect once compiled back into the cycle jar with `/opt/distro/scripts/offline-rebuild.sh`. Ledger lines should carry unit_id, state, reason_code, and source_day; the audit file should include version and entries with unit_id, auth_id, decision, and precedence_rank; affected-unit rows should carry unit_id, store_id, exposure_class, and qty_cases.

Audit precedence_rank: lower numbers mark stronger governing feeds. An ACTIVE recall notice requires rank 1 on that unit's signoff audit line (notice outranks grant). Absent signoff uses 99. Other cases use a positive composite rank from the contributing feeds.
