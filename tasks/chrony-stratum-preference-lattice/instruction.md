Seat the time desk so `/app/ops/run_time_seat.sh` emits `/output/time-seat.json`. The report carries schema_tag, a sources array, preference, sync_ok, and offset_bound_ms; each sources row carries name, stratum, selected, and hold.

Live chrony and timesync materials sit under `/etc/chrony/`, `/etc/systemd/timesyncd.conf.d/` (including `40-lab.conf`), and `/var/lib/chrony/`. Ops materials live under `/var/lib/time/ops/` (including `/var/lib/time/ops/prefer.toml`). `/usr/local/bin/timehealth` may look synchronized when seating truth does not. Stratum bands live under `/app/docs/time_bands.md`; seating outcomes under `/app/docs/seating_contract.md`. Template chrony peers used by seating live under `/app/config/chrony/sources.d`.

Do not rewrite frozen samples under `/app/data/sources/`. Running the seating entrypoint twice must yield byte-identical output.
