# sync operator reference

Leaf payloads live under `/app/data/leaves/` as JSON objects with `id`, `payload`, and `since` fields.
Journal tiers under `/app/data/journal/` record promoted generations. Runtime state is under `/app/data/state/runtime.json`.
Operator tables under `/app/config/l7/` are TOML files read at runtime by the lane and sync tools.

Rebuild `/app/bin/lane` from `/app/lane/` and `/app/bin/syncctl` from `/app/tree/`.

## Commands

`syncctl report --out PATH` writes a JSON object with integer `branch_gen`, hex string `root_digest`, and a `leaves` map of leaf id to hex digest.
`lane head` prints the checkpoint generation the lane module selects.
`/app/ops/scripts/digest_lab.py BRANCH` prints fixture-derived leaf and root digests for a branch generation.
