# Admit ledger schema

`/output/admit-ledger.json` is a JSON object with:

- `schema_version`: string, must be `edge-admit-1`
- `reload_epoch`: non-negative integer
- `cases`: array of objects, each with `id`, `decision`, `reason_code`

`decision` is `accept` or `reject`.

`reason_code` tokens produced by the admission path:

- `ok_aligned` — store generation, pin lineage, and capability checks all pass
- `gen_skew` — store generation does not match the live runtime epoch
- `lineage_skew` — subject/claim lineage does not match the active pin set
- `conflict` — generation and lineage checks both fail
- `stale_cache` — a refresh of previously cached-ok material is refused because
  the token is listed in the current revocation set (`refresh` set,
  `cached_ok` set, and current-list hit). Use this instead of `revoked` for
  that overlap.
- `revoked` — current-list hit outside the refresh+cached-ok window above

Generation and lineage outcomes are scored before capability reason codes.
