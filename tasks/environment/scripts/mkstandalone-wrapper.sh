#!/usr/bin/env bash
set -euo pipefail
/opt/lab/bin/mkstandalone --src /data/standby/replica.db --dst /data/standby/live.db
