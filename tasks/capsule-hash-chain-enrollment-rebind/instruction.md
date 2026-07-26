Device update capsules under /app enroll through a local stack. A key rotation and a partial revoke left the fleet inconsistent. Some capsules look good on a local check but enrollment refuses them on a host reload. Sibling devices disagree on the same capsule family. /app/bin/surfcheck often reports OK while the enrollment path later rejects (or the reverse).

Produce /output/enroll-ledger.json covering every scenario under /app/data/scenarios/. The ledger needs schema_version capsule-enroll-1, a cases array with id, device_id, decision (accept or reject), and reason_code on each row, plus reload_epoch equal to the epoch value in /app/data/state/runtime.json. Running /app/scripts/host-reload.sh and then /app/scripts/run-enroll.sh again must keep the same decisions and the same reload_epoch. The runtime epoch in /app/data/state/runtime.json must also stay put across that reload.

Use reason_code values from this set: stale_chain, revoked, gen_skew, ok_bound. Signature-only surface OK is not enrollment authority.

Leave /app/bin/surfcheck, /app/scripts/run-enroll.sh, and /app/data/scenarios/ in place and unmodified. Rebuild with make, then run /app/scripts/run-enroll.sh.
