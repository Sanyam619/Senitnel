Reconciliation Contract
=======================

Recovery must produce:

1. `/output/reconciliation.json` — top-level object with an `episodes`
   map. Every crash-export name under `/app/data/episodes/` must appear
   as a key.

2. `/output/restored/<name>/` for each episode, containing:
   - `payload.bin`
   - `fragments.bin`
   - `report.json` (local roster / peer / decision mirror for operators)

3. `/output/meta/run.stamp` — written by a successful recovery pass;
   records the armed policy tokens used for that run.

Each `episodes.<name>` object carries:

- `roster_final` — sorted list of lab name strings. Coordinator `seal`
  epoch is the roster fence: later `admit`/`reclaim` rows stay provisional
  and must not enlarge this set.
- `borrow_peer` — string peer id, or JSON `null`. A claim qualifies only
  when it is live and its peer is not quarantined. Among qualifying
  claims, sealed ones take precedence; among those, the earliest `ts`
  wins.
- `payload_digest` — 64-char lowercase hex digest of restored `payload.bin`
- `fragment_digest` — 64-char lowercase hex digest of restored `fragments.bin`
- `decision` — short outcome label string for the episode

Digests are SHA-256 of the restored file bytes.

Live administration (crash-export JSON alone is not sufficient):

- Effective policy at `/etc/fleet/reconcile.conf` is produced by folding
  `/etc/fleet/reconcile.d/*.conf` in lexical filename order (later files
  override earlier keys). Synonym tokens are not equivalent to site
  standard. The folded result must match `/etc/fleet/site_standard.conf`
  exactly on `precedence_mode`, `borrow_gate`, and `fragment_order`.
- Abort-window residue under `/var/lib/fleet/ops/abort.d/` rematerializes
  into live drop-ins on every recovery pass unless a durable cutover
  receipt exists at `/var/lib/fleet/state/cutover.ok`. The receipt is a
  plain `key=value` text file (not JSON) with exactly these keys on their
  own lines: `gen=<target>`, `hold=<sealed-cutover-hold>`, and `mode=seal`.
  A matching receipt skips rematerialize; it does **not** mean delete the
  live drop-in. `/etc/fleet/reconcile.d/90-local.conf` must remain present
  after recovery and must carry site-standard
  `precedence_mode` / `borrow_gate` / `fragment_order` values (rewrite those
  live drop-in synonyms in place). The abort package itself
  (`/var/lib/fleet/ops/abort.d/90-local.conf`) is forensic abort-window
  residue: it must stay present and keep its original synonym tokens
  (`prefer_seal` / `live_or_clear` / `byte_offset`). Do not rewrite the
  abort package to site-standard; skipping rematerialize leaves that
  residue alone. Without a matching receipt, synonym abort residue returns
  onto the live drop-in and the fold diverges from site standard again.
- Ops journal at `/var/lib/fleet/ops/journal.jsonl` records cutover and
  rollback rows. The sealed cutover for `/var/lib/fleet/state/gen.target`
  is authoritative over provisional rollback rows (including later ones).
  After journal apply, `gen.live` equals `gen.target`,
  `/var/lib/fleet/state/attach.intent` contains the exact raw journal mode
  token `seal` (not `sealed`), and the armed hold token matches that
  sealed cutover.
- `PAYLOAD_LINEAGE` in `/etc/fleet/fleetd.env` must name a real volume
  subdirectory under `/var/lib/fleet/volumes/<episode>/` — for sealed
  authority that directory is `sealed`. The journal mode token `seal` is
  not a directory name; writing it into `PAYLOAD_LINEAGE` misarms the
  supervisor and undoes sealed same-inode attaches. Keep
  `attach.intent=seal` distinct from `PAYLOAD_LINEAGE=sealed`.
- Lease bags under `/var/lib/fleet/leases/` and quarantine flag files under
  `/var/run/fleet/gate/<episode>/<peer>` must reflect crash-export maps
  once generation is aligned. File presence under the gate path means
  quarantined.
- Runtime payload at `/var/lib/fleet/runtime/<episode>/payload.bin` must
  be a same-inode attach of
  `/var/lib/fleet/volumes/<episode>/sealed/payload.bin`, with `.hold`
  carrying the armed sealed-cutover hold token. Supervisor refresh copies
  bytes when holds/lineage disagree; it does not invent sealed hardlinks.
- `/app/ops/fleetd` must be running (`/var/run/fleet/fleetd.pid`).

The recovery entrypoint is `/app/ops/run_recovery.sh`. Hand-placed
`/output` trees that skip that entrypoint will not survive verification.

Do not modify `/app/data/` (crash-export bytes must match
`/app/packaging/episodes.sha256`). Leave `/app/bin/fleetpeek` byte-identical
to the digest recorded under `/app/packaging/fleetpeek.sha256`.
