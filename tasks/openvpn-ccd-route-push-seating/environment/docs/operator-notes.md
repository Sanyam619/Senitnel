Operator notes
==============

Surface readiness tools under `/usr/local/bin/` only check whether CCD
directories and roster sheets exist. They do not validate tip journals,
pool preference, abort receipts, or generation floors. Treat connected
output as a liveness probe, not seating authority.

Pool CIDRs may overlap across sheets. Prefer-selected durable materials
decide which overlapping pool stays active after seating.
