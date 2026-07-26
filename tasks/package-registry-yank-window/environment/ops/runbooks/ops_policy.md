# Index yank and advisory policy

Index snapshots under `/app/data/index/snapshots/` promote a generation.
Yank windows live in `/app/data/yanks/windows.jsonl`.
Revoke rows live in `/app/data/yanks/revokes.jsonl`.

## Active yank

A crate version is under an active yank at generation G when all of
the following hold:

1. A window exists with `from <= G`.
2. The window's upper bound is open-ended (`until` null) or exclusive
   (`G < until`). A window that ends at generation N is not active at N.
3. No revoke row for that crate version has `at <= G`.

## Installability

A published version is installable at G when it is not under an active
yank and every *required* dependency edge leads to an installable
version. Dependency edges marked `"kind": "optional"` do not block.
Blocking follows the full required dependency chain, not only the
direct edge.

## Advisories

Advisory feed rows under `/app/data/advisories/feed.jsonl` contribute
to the advisory digest only when:

- the matching crate version is under an active yank at G, and
- the row's severity meets the operator floor `high` in `/app/config/l7/`
  (`critical` > `high` > `medium` > `low`).

Rows for ended or revoked windows must not appear. Rows below the
severity floor must not appear even if the yank is live.

## Tools

- `advscan window` — promoted snapshot generation
- `advscan digest` — advisory digest for that generation
- `indexctl report --out PATH` — reconcile document for the active generation

Operator tables under `/app/config/l7/` select bound mode, revoke honor,
live-only advisory filtering, and the severity floor. The verifier accepts
only the following literal token values in `/app/config/l7/k9.toml`:

- `bound_mode = "half_open"` — the only token that arms exclusive-upper /
  open-ended semantics; other spellings (for example `"halfopen"`,
  `"exclusive_upper"`, `"open"`) are rejected even if the runtime honors
  the same behavior.
- `honor_revokes = true`
- `adv_live_only = true`
- `adv_floor = "high"` (`critical` > `high` > `medium` > `low`)

## Input integrity

Do not rewrite fixture inputs under `/app/data/crates/`, `/app/data/yanks/`,
`/app/data/advisories/`, or `/app/data/index/snapshots/`. The verifier keeps
its own SHA-256 ledger for those bytes; any drift fails the run.
