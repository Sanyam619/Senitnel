# Ledger notes

The enrollment pass writes a single JSON document. Top level fields:

- `schema_version` — a fixed identifier for this ledger shape.
- `reload_epoch` — the epoch the pass bound against.
- `cases` — one entry per scenario.

Each case entry carries:

- `id` — the scenario id.
- `device_id` — the device the scenario belongs to.
- `decision` — whether the record enrolled.
- `reason_code` — a short token describing why.

## Record encoding

Records under `data/capsules/` use a line-oriented `key=value` encoding with
`leaf`, `parent`, `sig`, and `gen` keys. The framing tool parses this shape and
reports the parsed fields plus its surface verdicts as JSON.

## Policy codes

`polgate` returns a numeric code on stdout as `{"code": N}`. Callers map the
code onto the reason vocabulary they expose in their own output.
