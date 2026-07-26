# Cutover contract

## Preference

Seat prep may wipe live preference drop-ins back to a shadow-only seed. Graded fold restores the sealed preference pack and folds drop-ins in lexical order (later assignments override earlier ones). The folded mode must be `equality-inclusive`. Preference arm `/var/lib/samba/meta/pref.armed` must carry the same value as `/etc/samba/desk.seal`.

## Tip / backend map

Graded tip authority is `/var/lib/samba/journal/tips.bin` (not plaintext `tips.jsonl`). Observation: `/app/bin/tipcheck`. Tips beyond the active desk seal must not drive the live backend. Tagged tips must not win. Among remaining tips, higher rank wins; equal ranks keep the later record. Successful seating writes `/var/lib/samba/meta/backends.toml` and `/var/lib/samba/meta/tip.ok` equal to the desk seal.

`/var/lib/samba/meta/backends.crash.toml` is a frozen stale crash record. Live `backends.toml` must differ from it; the crash decoy backend must not remain as the live folded kn. Seat rematerialize that re-applies the crash map on every pass must not remain armed after cutover.

## Ops journal cutover

Graded ops authority is `/var/lib/samba/ops/journal.bin` (not plaintext `journal.jsonl`). Observation: `/app/bin/jrnlcheck`. The sealed maintenance cutover for `/var/lib/samba/meta/gen.target` determines hold and lineage. `attach.intent` is the raw token `seal`. `PAYLOAD_LINEAGE` names the sealed volume directory (not the journal mode token). Durable `/var/lib/samba/meta/cutover.ok` carries `gen=`, `hold=`, and `mode=seal`. `cut.arm` and `gen.live` equal desk.seal.

Abort packages and the reload hammer rematerialize onto live drop-ins only when durable cutover arm is missing. After a successful cutover+reload cycle, `/etc/samba/smb.conf.d/40-legacy.conf` must remain present and must differ in content from `/var/lib/samba/journal/legacy.prefer`.

## Attach / scrub / report

Flat `/var/lib/samba/attach/<name>.bin` same-inode hardlinks to sealed shelves under `/var/lib/samba/origins/`. Nested or decoy copies fail desk refresh. Host markers under `/var/lib/samba/volumes/*/host/` and torn leases under `/var/run/samba/` must be absent when `gen.live` equals `gen.target`.

Abort rematerialize onto live drop-ins is suppressed only when durable `cutover.ok` matches target gen, hold, and `mode=seal`; suppression keeps the live abort-window drop-in present rather than deleting it.

Report fields: `status`, `backend`, `seal_gen`, `principals[]` with `name`, `sid`, `uid`, `gid`, `range`.
