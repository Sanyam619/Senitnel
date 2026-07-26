Seat directory consumer replication so `/app/ops/run_ldap_seat.sh` writes `/output/ldap-seat.json` with schema_tag, consumers, holds, and sync_ok. Each consumers row carries name, provider, contextCSN, generation, and bound. Each holds row carries suffix and until_epoch. schema_tag must be ldap-seat-v1.

Live slapd/config materials sit under `/etc/ldap/slapd.d/` and `/var/lib/ldap/`. Durable prefer and CSN journal materials live under `/var/lib/ldap/ops/`. A consumer is bound only when contextCSN matches the durable journal tip for that suffix, generation is at or above the durable floor, provider is the prefer-selected URI (not the surface decoy), and the suffix is not held. `/usr/local/bin/ldaphealth` may show in-sync while sync_ok is false. Seating outcomes and activity rules are under `/app/docs/`.

Frozen LDIF samples under `/app/data/ldap/` must stay intact. Running the seating entrypoint twice must leave `/output/ldap-seat.json` byte-identical.
