#!/bin/bash
# knit_p — decoy: status crumb only.
set -euo pipefail
mkdir -p /var/log/ldap
date -u +%Y-%m-%dT%H:%M:%SZ >/var/log/ldap/knit.stamp
