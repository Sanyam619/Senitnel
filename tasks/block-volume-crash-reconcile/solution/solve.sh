#!/bin/bash
set -euo pipefail

mkdir -p /output
cd /opt/kvfs

cat > ops/apply_site_policy.sh <<'APPLYEOF'
#!/bin/bash
set -euo pipefail

SITE_INI="/opt/kvfs/config/recovery_policy.ini"
BACKUP="${SITE_INI}.pre-kvfs441"
REFRESH_MARK="/opt/kvfs/config/.policy_refresh.stamp"
LOG_PREFIX="[kvfs-site-policy]"

log() {
  echo "$LOG_PREFIX $*"
}

require_config_dir() {
  if [[ ! -d /opt/kvfs/config ]]; then
    log "config directory missing"
    exit 1
  fi
}

backup_current_policy() {
  if [[ -f "$SITE_INI" ]]; then
    cp -a "$SITE_INI" "$BACKUP"
    log "saved prior policy to $(basename "$BACKUP")"
  fi
}

write_policy_bundle() {
  cat > "$SITE_INI" <<'EOF'
# KVFS batch recovery policy — site standard after crash review
[replay]
order=tx_id
forget_mode=invalidate_earlier

[bitmap]
metadata_used_end=28

[image]
patch_zero_pad=1
preserve_superblocks=1

[header]
prefer=epoch
EOF
}

stamp_refresh() {
  date -u +%Y-%m-%dT%H:%M:%SZ > "$REFRESH_MARK"
  log "policy refresh stamped"
}

require_config_dir
backup_current_policy
write_policy_bundle
stamp_refresh
log "site policy bundle applied"
APPLYEOF
chmod +x ops/apply_site_policy.sh

cat > ops/run_recovery.sh <<'RUNEOF'
#!/bin/bash
set -euo pipefail
cd /opt/kvfs
if [[ ! -x ops/apply_site_policy.sh ]]; then
  echo "missing apply_site_policy.sh" >&2
  exit 1
fi
./ops/apply_site_policy.sh
if [[ ! -f config/recovery_policy.ini ]]; then
  echo "policy missing after apply" >&2
  exit 1
fi
rm -f bin/reconcile lib/m3_apply.o lib/p7_sb.o
make bin/reconcile
mkdir -p /output
bin/reconcile
RUNEOF
chmod +x ops/run_recovery.sh

cp /solution/patch/m3_apply.c lib/m3_apply.c
cp /solution/patch/reconcile.c tools/reconcile.c
cp /solution/patch/p7_sb.c lib/p7_sb.c

ops/run_recovery.sh
