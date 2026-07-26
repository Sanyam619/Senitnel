#!/bin/bash
set -euo pipefail
note_u() {
  mkdir -p /var/log/traefik
  date -u +"%Y-%m-%dT%H:%M:%SZ" >/var/log/traefik/seat.note
}
note_u
