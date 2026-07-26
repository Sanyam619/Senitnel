# IPA client seating — normal layout

/etc/krb5.conf.d/
  Drop-in realm preference fragments. Effective realm is the lexical fold of *.conf.

/etc/sssd/
  Live sssd.conf plus per-host domain abort drop-ins under conf.d/.

/etc/ipa/floors/
  Live tip floor sheets. Surface health may read here; not durable authority.

/var/lib/ipa/
  Per-host directories with keytab fingerprint crumbs and entry samples, durable
  floors under floors/, enrollment journal and preference accept under ops/,
  runtime state under state/ including /var/lib/ipa/state/tip_id and verifier
  seating fingerprints /var/lib/ipa/state/seat_pass_a.bin and
  /var/lib/ipa/state/seat_pass_b.bin.

/app/data/ipa/
  Frozen keytab samples. Packaging digest under /app/packaging/ipa.sha256.

/app/ops/run_ipa_seat.sh
  Operator seating entrypoint.

/usr/local/bin/ipahealth
  Surface health probe. Green does not imply deep enrollment agreement.
