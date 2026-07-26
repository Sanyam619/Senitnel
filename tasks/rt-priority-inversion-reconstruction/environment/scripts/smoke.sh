#!/bin/sh
set -e
/opt/kernlab/bin/kernprobe --manifest /opt/kernlab/config/manifest.txt --out /tmp/smoke.json
test -s /tmp/smoke.json
