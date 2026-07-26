Operator notes
==============

Surface health via `proxyhealth` only checks that the admin trees exist.
It does not validate fold, drain leases, journal tips, or runtime
socket apply. Prefer the seating entrypoint and the ledger under
`/output/proxy-seat.json` when confirming deep seating.

Roster names are listed in `/etc/haproxy/roster.list`. Durable addresses
are under `/var/lib/haproxy/backends/`.
