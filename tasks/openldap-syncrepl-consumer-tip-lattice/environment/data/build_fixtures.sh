#!/bin/bash
# Materialize live /etc and /var from seed fixtures; pin LDIF digest.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data"
SEED="$DATA/seed"

mkdir -p /etc/ldap/prefer.d /etc/ldap/floors /etc/ldap/slapd.d/cn=config \
  /var/lib/ldap/floors /var/lib/ldap/holds /var/lib/ldap/ops \
  /var/lib/ldap/state /var/run/ldap /var/log/ldap /output

cp -a "$DATA/roster.list" /etc/ldap/roster.list
cp -a "$SEED/prefer.d/." /etc/ldap/prefer.d/
cp -a "$SEED/slapd.d/." /etc/ldap/slapd.d/
cp -a "$SEED/journal.jsonl" /var/lib/ldap/ops/csn_journal.jsonl
cp -a "$SEED/surface.uri" /var/lib/ldap/ops/surface.uri
cp -a "$SEED/clock.epoch" /var/lib/ldap/state/clock.epoch
printf '7\n' >/var/lib/ldap/state/gen.target
printf '3\n' >/var/lib/ldap/state/gen.live
printf 'tip_live\n' >/var/lib/ldap/ops/prefer.accept
# prefer.accept as key=value for fairness (overwrite)
cat >/var/lib/ldap/ops/prefer.accept <<'EOF'
tip=tip_live
EOF

# Durable floors
while IFS='=' read -r k v; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  printf '%s\n' "$v" >"/var/lib/ldap/floors/${k}.floor"
done <"$SEED/floors.toml"

# Live decoy floors
while IFS='=' read -r k v; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  printf '%s\n' "$v" >"/etc/ldap/floors/${k}.floor"
done <"$SEED/live_floors.toml"

# Holds with suffix
while IFS='=' read -r k v; do
  [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
  suffix="dc=${k},dc=lab"
  {
    printf 'until_epoch=%s\n' "$v"
    printf 'suffix=%s\n' "$suffix"
  } >"/var/lib/ldap/holds/${k}.hold"
done <"$SEED/holds.toml"

# Live contextCSN crumbs (disagree with sealed tip — tip_live bait)
for n in alpha beta gamma delta epsilon; do
  mkdir -p "/var/lib/ldap/${n}"
  printf '20990101000000.999999Z#00live#000#000000\n' >"/var/lib/ldap/${n}/contextCSN"
  # entry count bait matching LDIF lines roughly
  cp -a "$DATA/ldap/${n}.ldif" "/var/lib/ldap/${n}/entries.ldif"
done

# Packaging digest for immutable fixtures
(
  cd "$DATA/ldap"
  sha256sum *.ldif | sort -k2
) >"$ROOT/packaging/ldap.sha256"

cp -a "$ROOT/packaging/ldap.sha256" /app/packaging/ldap.sha256 2>/dev/null || true
