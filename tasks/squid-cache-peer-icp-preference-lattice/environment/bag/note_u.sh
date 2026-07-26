#!/bin/bash
set -euo pipefail
# Appends a short operator note for desk logs.
note_u() {
  mkdir -p /var/log/squid
  date +%s >>/var/log/squid/operator.note
}
note_u
