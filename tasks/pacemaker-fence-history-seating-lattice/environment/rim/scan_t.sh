#!/bin/bash
# scan_t — surface inventory for crmhealth.
set -euo pipefail
INV=/var/log/cluster/inventory.log
mkdir -p "$(dirname "$INV")"
{
  echo "nodes=$(wc -l </var/lib/pacemaker/nodes.roster | tr -d ' ')"
  echo "resources=$(wc -l </var/lib/pacemaker/resources.roster | tr -d ' ')"
  echo "surface=ready"
} >"$INV"
