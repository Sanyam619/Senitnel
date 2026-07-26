# Layout

- `/etc/chrony/` — live chrony configuration and `sources.d`
- `/etc/systemd/timesyncd.conf.d/` — timesync drop-ins (lexical fold)
- `/var/lib/chrony/` — chrony state including hold window copy
- `/var/lib/time/ops/` — durable prefer, roster, authority, offsets
- `/var/lib/time/surface/` — surface seeds used when preference is not durable
- `/app/ops/run_time_seat.sh` — seating entrypoint
- `/app/config/chrony/sources.d` — template chrony peers used when seating binds live sources
- `/app/data/sources/` — frozen samples (do not rewrite)
- `/usr/local/bin/timehealth` — surface status helper
