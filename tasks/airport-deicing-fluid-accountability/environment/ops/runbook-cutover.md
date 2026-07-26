# Ramp batch cutover runbook

## Symptoms
Packaged shifts emit wrong ledger and compliance packs. Health still green.

## Surfaces
- `/opt/ramp/scripts/run-shift.sh`
- `/opt/ramp/config/ramp.conf` and `ramp.conf.cutover.bak`
- `/opt/ramp/bin/rampd` link target
- `/opt/ramp/systemd/ramp-batch.service`

## Non-goals
Do not edit `/data/fixtures`.
