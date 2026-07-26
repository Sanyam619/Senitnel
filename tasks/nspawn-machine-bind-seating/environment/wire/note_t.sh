#!/bin/bash
note_t() {
  set -euo pipefail
  mkdir -p /var/run/machines
  printf 'surface=ok\n' >/var/run/machines/surface.stamp
}
note_t
