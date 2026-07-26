#!/bin/bash
# Materialize live /etc and /var client materials from seed fixtures; pin sample digest.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data"
SEED="$DATA/seed"

mkdir -p /etc/ipa /etc/ipa/floors /etc/krb5.conf.d /etc/sssd/conf.d \
  /var/lib/ipa/floors /var/lib/ipa/ops \
  /var/lib/ipa/state /var/run/ipa /var/log/ipa /output

cp -a "$DATA/hosts.list" /etc/ipa/hosts.list
cp -a "$DATA/services.list" /etc/ipa/services.list
cp -a "$SEED/krb5.conf.d/." /etc/krb5.conf.d/
cp -a "$SEED/sssd.conf" /etc/sssd/sssd.conf
cp -a "$SEED/journal.jsonl" /var/lib/ipa/ops/enroll_journal.jsonl
cp -a "$SEED/surface.realm" /var/lib/ipa/ops/surface.realm
cp -a "$SEED/clock.epoch" /var/lib/ipa/state/clock.epoch
printf '7\n' >/var/lib/ipa/state/gen.target
printf '3\n' >/var/lib/ipa/state/gen.live

cat >/var/lib/ipa/ops/prefer.accept <<'EOF'
tip=tip_live
EOF

# Durable floors
while IFS='=' read -r k v; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  printf '%s\n' "$v" >"/var/lib/ipa/floors/${k}.floor"
done <"$SEED/floors.toml"

# Live floor sheets (surface health may read here)
while IFS='=' read -r k v; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  printf '%s\n' "$v" >"/etc/ipa/floors/${k}.floor"
done <"$SEED/live_floors.toml"

# SSSD domain abort drop-ins
while IFS='=' read -r k v; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  {
    printf 'host=%s\n' "$k"
    printf 'abort_until=%s\n' "$v"
  } >"/etc/sssd/conf.d/${k}.conf"
done <"$SEED/aborts.toml"

# Live keytab fingerprint crumbs and entry samples
for n in web01 db01 cache01 mail01 log01; do
  mkdir -p "/var/lib/ipa/${n}"
  printf '000000000live\n' >"/var/lib/ipa/${n}/keytab.fpr"
  cp -a "$DATA/ipa/${n}.info" "/var/lib/ipa/${n}/entries.info"
done

# Packaging digest for immutable samples
(
  cd "$DATA/ipa"
  sha256sum *.info | sort -k2
) >"$ROOT/packaging/ipa.sha256"

cp -a "$ROOT/packaging/ipa.sha256" /app/packaging/ipa.sha256 2>/dev/null || true
