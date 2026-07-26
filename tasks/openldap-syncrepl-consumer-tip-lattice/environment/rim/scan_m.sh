#!/bin/bash
# scan_m — surface entry-count helper for ldaphealth.
set -euo pipefail
ROOT="${LDAP_ROOT:-/var/lib/ldap}"
ROSTER="${ROSTER:-/etc/ldap/roster.list}"
ok=1
while IFS=$'\t' read -r name suffix || [[ -n "${name:-}" ]]; do
  name="$(echo "${name:-}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [[ -z "$name" || "$name" =~ ^# ]] && continue
  live="$ROOT/${name}/entries.ldif"
  frozen="/app/data/ldap/${name}.ldif"
  if [[ ! -f "$live" || ! -f "$frozen" ]]; then
    ok=0
    continue
  fi
  lc=$(wc -l <"$live" | tr -d ' ')
  fc=$(wc -l <"$frozen" | tr -d ' ')
  if [[ "$lc" != "$fc" ]]; then
    ok=0
  fi
done <"$ROSTER"
exit $((1 - ok))
