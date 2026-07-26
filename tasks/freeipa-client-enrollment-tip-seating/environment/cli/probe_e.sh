#!/bin/bash
# probe_e — surface entry-count helper for ipahealth.
set -euo pipefail
ROOT="${IPA_ROOT:-/var/lib/ipa}"
HOSTS="${HOSTS:-/etc/ipa/hosts.list}"
ok=1
while IFS=$'\t' read -r name fqdn || [[ -n "${name:-}" ]]; do
  name="$(echo "${name:-}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [[ -z "$name" || "$name" =~ ^# ]] && continue
  live="$ROOT/${name}/entries.info"
  frozen="/app/data/ipa/${name}.info"
  if [[ ! -f "$live" || ! -f "$frozen" ]]; then
    ok=0
    continue
  fi
  lc=$(wc -l <"$live" | tr -d ' ')
  fc=$(wc -l <"$frozen" | tr -d ' ')
  if [[ "$lc" != "$fc" ]]; then
    ok=0
  fi
done <"$HOSTS"
exit $((1 - ok))
