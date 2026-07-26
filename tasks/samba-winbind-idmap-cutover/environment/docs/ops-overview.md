# Ops overview

Entrypoints:

- `/app/ops/run_idmapseat.sh` — prep rematerialize, preference, tip seating, cutover arm, abort gate, scrub, attach, desk refresh, binder
- `/app/ops/run_reload.sh` — reload path before seating again

Prebuilt:

- `/app/bin/idmapctl` — report + tdb from sealed attach seats
- `/app/bin/tipfold` / `/app/bin/cutarm` — tip seating and cutover arm
- `/app/bin/tipcheck` / `/app/bin/jrnlcheck` — observation dumps of opaque streams
- `/app/bin/wbinfo` / `/app/bin/smblist` — surface shims (smblist is not idmap authority)

Meta markers under `/var/lib/samba/meta/`: `backends.toml`, `backends.crash.toml` (frozen stale crash record), `tip.ok`, `gen.target` / `gen.live`, `attach.intent`, `cutover.ok`, `cut.arm`, `pref.armed`.

Opaque streams: `/var/lib/samba/journal/tips.bin`, `/var/lib/samba/ops/journal.bin`.
Plaintext `*.jsonl` beside them are not graded authority.

Seat prep rematerializes drifted preference, legacy, abort, and lineage surfaces before helpers run. Desk refresh undoes non-sealed attach seats and re-applies the reload hammer when durable cutover receipt is missing.
