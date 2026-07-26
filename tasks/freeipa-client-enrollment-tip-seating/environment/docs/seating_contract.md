Seating Contract
================

Graded seating produces `/output/ipa-seat.json`:

- `schema_tag` must be the literal string `ipa-seat-v1`
- `hosts` lists every roster host with `realm`, `keytab`, integer `generation`,
  and boolean `enrolled`
- `services` lists every service principal with boolean `bound`
- `seat_ok` is true only when every host's enrolled bit, realm, and keytab agree
  with durable authority. For example, `seat_ok` stays true when a host is
  correctly unenrolled by its floor or abort because that `enrolled` value still
  agrees with durable authority.

Activity rules
--------------

1. Durable floors live under `/var/lib/ipa/floors/<name>.floor` as a single
   integer. A tip generation at or above that floor may enroll (equality
   inclusive). Live sheets under `/etc/ipa/floors/` are not the durable
   authority.

2. SSSD domain abort windows live under `/etc/sssd/conf.d/<name>.conf` and carry
   `host` and `abort_until`. Compare against `/var/lib/ipa/state/clock.epoch`. An
   active window (`abort_until` greater than the desk clock) keeps the related
   host unenrolled. An expired window does not abort enrollment.

3. Drop-ins under `/etc/krb5.conf.d/` fold in lexical filename order; later files
   override earlier keys. The effective `realm` is the prefer-selected realm from
   site-standard materials (`LAB.EXAMPLE.ORG` in `/app/config/site_standard.conf`).
   The surface decoy realm under `/var/lib/ipa/ops/surface.realm` must not remain
   selected after seating. Each seating pass must materialize the completed fold
   at `/etc/ipa/effective.conf`, where `realm` equals that selected realm.

4. On every seating pass, the live SSSD domain stanza receives a realm. When
   `/var/lib/ipa/ops/prefer.accept` exists as plain `key=value` lines with exactly
   `tip=<tip_id>` matching the sealed journal tip id written to
   `/var/lib/ipa/state/tip_id` for `/var/lib/ipa/state/gen.target`, seating applies
   the prefer-selected realm from `/app/config/site_standard.conf`
   (`LAB.EXAMPLE.ORG`). Otherwise the surface decoy realm under
   `/var/lib/ipa/ops/surface.realm` is written in. A matching receipt does **not**
   mean delete live SSSD files. Seating must write `/var/lib/ipa/ops/prefer.accept`
   so its `tip` value matches the sealed tip selected for `gen.target`; treating
   that receipt as read-only is not a completed seating pass.

5. The enrollment journal under `/var/lib/ipa/ops/enroll_journal.jsonl` records tip
   and seal rows. The sealed cutover for `gen.target` (kind `seal`, mode `seal`) is
   authoritative for per-host keytab fingerprint and `generation` via its `tips`
   map. Newer live tip rows and on-disk keytab fingerprint crumbs under
   `/var/lib/ipa/<name>/` are not the durable tip. After apply, `gen.live` equals
   `gen.target`.

6. A host is enrolled only when all of: the durable tip fingerprint is published as
   `keytab`, generation is at or above the durable floor, realm equals the prefer-
   selected realm, and the host is not under an active SSSD abort.

7. A service is bound exactly when its host is enrolled.

8. Two sequential seating runs must leave byte-identical `/output/ipa-seat.json`.
