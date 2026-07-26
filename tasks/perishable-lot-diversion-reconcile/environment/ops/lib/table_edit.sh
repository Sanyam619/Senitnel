#!/bin/bash
set -euo pipefail
l7_dir="${L7_DIR:-/app/config/l7}"
set_field() { local file="$1" field="$2" value="$3"; sed -i "s/^${field} = .*/${field} = ${value}/" "${l7_dir}/${file}"; }
