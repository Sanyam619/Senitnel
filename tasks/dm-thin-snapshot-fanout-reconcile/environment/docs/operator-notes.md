Operator notes

Materialize runs from /app/ops/run_materialize.sh. Surface status is
available via /app/bin/dmhealth. Live pool state stays under /etc/pool and
/var/lib/pool; leases under /var/run/pool. Origin shelf payloads are read
during materialize and must remain byte-identical; lease marker files must
not remain under /var/lib/pool/origins/.

Preference drop-ins live under /etc/pool/pref.d/. Tip rows carry epoch and
floor values from the sealed journal; the active preference mode decides
whether a tip materializes as cow or live. equality-inclusive is the mode
this lab expects.

Journal lines and tip shelves may exist for drills that are not on the
active roster; fanout should follow the roster and the sealed activation
journal, not every shelf that happens to be present.
