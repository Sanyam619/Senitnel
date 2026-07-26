# LDAP seating — normal layout

/etc/ldap/prefer.d/
  Drop-in preference fragments. Effective provider URI is the lexical fold of *.conf.

/etc/ldap/slapd.d/
  Live cn=config tree including consumer syncrepl stanzas.

/etc/ldap/floors/
  Live tip floor sheets. Surface health may read here; not durable authority.

/var/lib/ldap/
  Per-suffix database directories with contextCSN crumbs, durable floors under
  floors/, hold windows under holds/ (e.g. gamma.hold, delta.hold), ops journal
  and preference accept under ops/, runtime state under state/ including
  /var/lib/ldap/state/tip_id and verifier seating fingerprints
  /var/lib/ldap/state/seat_pass_a.bin and /var/lib/ldap/state/seat_pass_b.bin.

/app/data/ldap/
  Frozen LDIF samples. Packaging digest under /app/packaging/ldap.sha256.

/app/ops/run_ldap_seat.sh
  Operator seating entrypoint.

/usr/local/bin/ldaphealth
  Surface health probe. Green does not imply deep sync agreement.
