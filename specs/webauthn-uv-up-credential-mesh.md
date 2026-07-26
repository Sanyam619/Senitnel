# Authoring Brief — webauthn-uv-up-credential-mesh

## Category redesign

Moved from `security` / Rust source repair to **system-administration**.

Primary graded activity is operating live `/etc/ceremony/` and
`/var/lib/ceremony/` through `/app/ops/` helpers plus a prebuilt
`/app/bin/trusteval`. Agents must not rewrite Rust application sources;
sources build only in the Dockerfile builder stage and are stripped from
the runtime image.

`data-processing` is blocked and was not used. Category choice is
system-administration because the frontier is live drop-in fold, UV/UP
policy seating, hold/stream state files, abort rematerialize vs cutover
receipt, and ops re-entry — not schema transforms or offline ETL.

## Hardness shape

- Broken bash helpers reseat wrong UV/UP, inclusive hold bound,
  jsonl-then-wal stream order, and unconditional abort rematerialize.
- Correct binary honors folded live authority, exclusive hold, interleaved
  replay, and UV/UP profile requirements.
- Surface `jarcheck` / `ceremonyd_health` remains false-green bait.
- No SoftHSM rematerialize / tip_bind / trial_pref clones; no greppable
  polarity stubs with intent comments.

## Languages / tags

- `languages = ["bash"]`
- tags: ceremony-ops, dropin-policy, uv-up-seating, ops-journal, live-state,
  quarantine
