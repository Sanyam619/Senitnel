Operator notes
==============

Surface `/usr/local/bin/keahealth` only checks that `/etc/kea` and
`/var/lib/kea` trees exist. It does not validate lease collisions, pool
membership, or reservation honor. Treat a green surface check as
non-authoritative for seating.

Roster subnet ids live in `/etc/kea/roster.list`. Frozen fixture TOML
under `/app/data/kea/` must stay byte-identical to the packaging pin.
