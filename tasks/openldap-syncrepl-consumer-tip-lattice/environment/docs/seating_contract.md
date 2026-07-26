Seating Contract
================

Graded seating produces `/output/ldap-seat.json`:

- `schema_tag` must be the literal string `ldap-seat-v1`
- `consumers` lists every roster name with `provider`, `contextCSN`, integer
  `generation`, and boolean `bound`
- `holds` lists every hold window as `{suffix, until_epoch}`
- `sync_ok` is true only when every roster consumer's bound bit, provider, and
  contextCSN agree with durable authority. For example, `sync_ok` stays true
  when a consumer is correctly unbound by its floor or hold because that
  `bound` value still agrees with durable authority.

Activity rules
--------------

1. Durable floors live under `/var/lib/ldap/floors/<name>.floor` as a single
   integer. A tip generation at or above that floor may be bound (equality
   inclusive). Live sheets under `/etc/ldap/floors/` are not the durable
   authority.

2. Hold windows under `/var/lib/ldap/holds/<name>.hold` (for example
   `gamma.hold`, `delta.hold`) carry `until_epoch` and `suffix`. Compare against
   `/var/lib/ldap/state/clock.epoch`. An active window (`until_epoch` greater
   than the desk clock) keeps the related consumer unbound. Holds still appear
   in the `holds` array. An expired window does not block binding.

3. Drop-ins under `/etc/ldap/prefer.d/` fold in lexical filename order; later
   files override earlier keys. The effective `providerURI` is the prefer-
   selected provider from site-standard materials
   (`ldap://provider-a.lab:389` in `/app/config/site_standard.conf`). The
   surface decoy URI under `/var/lib/ldap/ops/surface.uri` must not remain
   selected after seating. Each seating pass must materialize the completed
   fold at `/etc/ldap/effective.conf`, where `providerURI` equals that selected
   provider.

4. On every seating pass, slapd.d consumer stanzas receive a provider URI.
   When `/var/lib/ldap/ops/prefer.accept` exists as plain `key=value` lines
   with exactly `tip=<tip_id>` matching the sealed journal tip id written to
   `/var/lib/ldap/state/tip_id` for `/var/lib/ldap/state/gen.target`, seating
   applies the prefer-selected providerURI from `/app/config/site_standard.conf`
   (`ldap://provider-a.lab:389`). Otherwise the surface decoy URI under
   `/var/lib/ldap/ops/surface.uri` is written in. A matching receipt does
   **not** mean delete live slapd.d files. Seating must write
   `/var/lib/ldap/ops/prefer.accept` so its `tip` value matches the sealed tip
   selected for `gen.target`; treating that receipt as read-only is not a
   completed seating pass.

5. Ops journal under `/var/lib/ldap/ops/csn_journal.jsonl` records tip and seal
   rows. The sealed cutover for `gen.target` (kind `seal`, mode `seal`) is
   authoritative for per-consumer `contextCSN` and `generation` via its `tips`
   map. Newer live tip rows and on-disk contextCSN crumbs under
   `/var/lib/ldap/<name>/` are not the durable tip. After apply, `gen.live`
   equals `gen.target`.

6. A consumer is bound only when all of: durable tip CSN is published as
   `contextCSN`, generation ≥ durable floor, provider equals the prefer-
   selected URI, and the suffix is not under an active hold.

7. Two sequential seating runs must leave byte-identical
   `/output/ldap-seat.json`.
