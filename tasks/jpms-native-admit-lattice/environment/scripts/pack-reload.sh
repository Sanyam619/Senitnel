#!/bin/bash
set -euo pipefail
# Soft reload: re-read durable materials and re-emit without resetting epoch.
/opt/desk/bin/holdrun >/tmp/holdrun.out
/opt/desk/bin/admitctl
