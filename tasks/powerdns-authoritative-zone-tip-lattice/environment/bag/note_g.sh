#!/bin/bash
set -euo pipefail
# Appends a short operator note for desk logs.
note_g() {
  mkdir -p /var/log/powerdns
  date +%s >>/var/log/powerdns/operator.note
}
note_g
