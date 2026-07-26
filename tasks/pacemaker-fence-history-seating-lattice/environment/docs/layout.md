Layout
======

- `/etc/corosync/` — live membership sheets (may drift)
- `/etc/pacemaker/cib.d/` — live CIB drop-ins (lexical fold)
- `/var/lib/pacemaker/` — durable floors, resource sheets, published state
- `/var/lib/cluster/ops/` — prefer journal, fence journal, abort.d, cutover state
- `/app/data/cluster/` — frozen roster fixtures (packaging-pinned)
- `/app/ops/run_crm_seat.sh` — seating entrypoint
- `/usr/local/bin/crmhealth` — surface health only
