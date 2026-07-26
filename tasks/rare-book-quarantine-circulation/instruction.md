The national archives circulation desk runs a Java batch job from `/opt/archives/scripts/run-cycle.sh`
with `--day <collection-day>` and `--root /data/fixtures`. It ingests quarantine feeds, covenant
feeds, exhibit feeds, RFID feeds, circulation feeds, and sweep maps, then writes
`/data/out/<day>/loan_decision_ledger.jsonl` (volume_id, decision, reason_code, collection_day),
`/data/out/<day>/quarantine_exceptions.json` (version, entries), and
`/data/out/<day>/shelf_custody_audit.tsv` (volume_id, branch_id, custody_class, request_qty).

Conservation policy refresh regressed the circulation batch. Active quarantine should deny loans even when a donor
covenant grants release; flagged volumes currently read loanable on those days. Unrelated reading-room units should
loan when their RFID sweep is in window; they currently read blocked. Cleared exhibit paperwork should open the
case; those sweeps currently read locked. Flagged parents should hold every bound sibling; siblings currently read
circulating. Identical collection-day reruns should produce stable shelf-custody audit bytes. A volume denied at
multiple branches needs one audit row per branch, not one row per volume.

Rebuild the Maven project under `/opt/archives`, rerun the cycle for every collection day present
under `/data/fixtures`, and leave those fixtures unchanged. Conservation auditors first spotted
symptoms on `day_c0901` through `day_c0905`.
