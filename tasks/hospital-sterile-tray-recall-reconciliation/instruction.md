Central sterile processing runs a Go batch from `/opt/csp/scripts/run-case.sh`
with `--case <case-name>` and `--root /data/fixtures`. Each case writes
`/data/out/<case>/quarantine_ledger.jsonl` (tray_id, state, reason_code,
source_case, seq), `/data/out/<case>/tray_disposition.json` (version, trays),
and `/data/out/<case>/recall_audit.tsv` (lot_id, trays_blocked, trays_cleared,
exposure_class).

Disposition precedence, notice timing, set inheritance, cycle-window checks,
and audit tally semantics are specified in `/opt/csp/config/disposition_policy.toml`.
A recent deploy no longer enforces that policy for cases `case_c0412` through
`case_c0418` using fixtures under `/data/fixtures`. Ledger, disposition, and
audit outputs for those cases must match the policy file on every run.
