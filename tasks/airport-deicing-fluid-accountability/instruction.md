You are covering the regional ramp winter cutover. The batch stack under `/opt/ramp/`
was left half wired: the live runner link points at the rollback build, a rehearsal
config overlay is applied at wrapper start, and `/opt/ramp/scripts/ramp-health.sh`
reports the runner present. Packaged shifts write bad reports, sometimes under the
staging tree instead of the live output tree.

Use `/opt/ramp/scripts/run-shift.sh --shift <name> --root /data/fixtures` to run a
shift. Each packaged shift must publish `/data/out/<shift>/fluid_ledger.jsonl`,
`/data/out/<shift>/runoff_compliance.json`, and
`/data/out/<shift>/truck_utilization_audit.tsv`. Ledger rows carry aircraft_id,
pad_id, gallons_applied, fluid_code, and seq. Compliance docs carry version and
tanks. Truck audits use truck_id, active_min, gallons_pumped, and efficiency_pct.
Full field lists live in `/opt/ramp/config/output-fields.txt`. Fresh files under
`/data/out/staging` mean the rehearsal output root is selected.

Ops notes and runtime fragments live under `/opt/ramp/config/`. Binaries live under
`/opt/ramp/bin/`. Packaged feeds under `/data/fixtures` are audit anchors — do not
modify them. Finish the cutover so the live layout runs the active runner with the
correct working directory, fixture root, and output root, then rerun every packaged
shift.
