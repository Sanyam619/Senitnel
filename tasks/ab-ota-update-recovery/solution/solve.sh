#!/bin/bash
set -euo pipefail

mkdir -p /output
cd /opt/abdev

cat > config/active_policy.toml <<'EOF'
# Rollout wave 3 policy table
rule_order=rollback_staging_b,repoint_live_b_fail,commit_staging_a,rollback_live_b_fail,hold
allow_commit=true
mirror_pick=generation
finalize_commit_gen=bump
verify_payload_chain=true
write_both_metadata_mirrors=true
write_both_control_mirrors=true
default_action=hold
retire_on_integrity_fail=true
clear_pending_on_rollback=true
promote_staging_boot_ok=1
swap_phase_idle=0
report_bootloader_mirror=0
scenario_batch=all
field_override=enabled
integrity_gate=strict
EOF

cat > config/recover.env <<'EOF'
# Environment consumed by ops/reconcile_field.sh
AB_POLICY_FILE=/opt/abdev/config/active_policy.toml
AB_DATA_ROOT=/opt/abdev/data/scenarios
AB_OUT_ROOT=/output
AB_REPORT=/output/recovery.json
AB_VERIFY_BOOTSIM=1
AB_PRESERVE_INPUTS=1
EOF

ops/reconcile_field.sh

for case in case_alpha case_beta case_gamma case_delta; do
  bin/bootsim "/output/fixed_${case}.img" >/dev/null
done
