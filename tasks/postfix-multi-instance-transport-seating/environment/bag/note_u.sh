#!/bin/bash
set -euo pipefail
# note_u — inventory stamp only
note_u() {
  date +%s >"${PF_VAR:-/var/lib/postfix}/state/note.stamp"
}
note_u
