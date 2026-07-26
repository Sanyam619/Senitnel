# Layout

- `/etc/multipath/multipath.conf` — base multipath defaults
- `/etc/multipath/conf.d/` — per-map weight drop-ins (folded lexically)
- `/var/lib/multipath/ops/` — durable prefer, roster, authority, holds
- `/var/lib/multipath/candidates/` — live per-map path substrate consumed by seating
- `/var/lib/multipath/bindings` — runtime seating written during the cutover
- `/app/ops/run_alua_seat.sh` — seating entrypoint
- `/app/data/sysfs/` — frozen remote-port fixtures mirrored from `/sys/class/fc_remote_ports` (do not rewrite)
- `/usr/local/bin/mpathhealth` — surface status helper
