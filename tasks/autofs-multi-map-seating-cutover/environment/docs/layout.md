# Autofs seating — normal layout

/etc/auto.master.d/
  Drop-in conf fragments. Effective policy is the lexical fold of *.conf.

/etc/autofs/
  Live tip views and surface-facing floor sheets. Surface health reads here.

/var/lib/autofs/
  Durable map copies under maps/, floors under floors/, hold windows under
  holds/, ops journal and abort package under ops/, runtime state under state/.

/app/data/maps/
  Frozen map fixtures. Packaging digest under /app/packaging/maps.sha256.

/app/ops/run_autofs_seat.sh
  Operator seating entrypoint.

/usr/local/bin/autofshealth
  Surface health probe. Green does not imply deep seating agreement.
