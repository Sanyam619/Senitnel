Seating Contract
================

Graded seating produces `/output/nft-seat.json`:

- `schema_tag` must be the literal string `nft-seat-v1`
- `tables` lists **every roster name** from `/etc/nft/roster.list` with
  `family`, `name`, and integer `generation` — including tables whose tip
  sits below the durable floor. Under-floor tables stay out of the applied
  fold and out of `chains`, but they still appear in `tables` with the sealed
  tip generation.
- `chains` lists every chain present in the applied fold with `table`, `name`,
  `policy`, `hook`, and integer `priority`
- `rules_applied` counts concrete nftables rule statements in the applied
  fold only (not blank lines, comments, braces, `table` / `chain` headers, or
  `type … hook … policy …` lines). Plain `key=value` operator memos are not
  rules and must not be folded into the ruleset.
- `seat_ok` is true only when fold, prefer, apply, round-trip, and live
  generation marker all agree

Fold and apply rules
--------------------

1. Fragments under `/etc/nftables.d/` fold in lexical filename order into
   `/var/lib/nft/ops/fold.nft`. A later abort fragment must be excluded from
   the durable fold. Fragments whose table tip is below the durable floor are
   also excluded from the fold (and from `chains`), not from the `tables`
   roster list.

2. Durable floors live under `/var/lib/nft/floors/<name>.floor` as a single
   integer. Tip generations come from the sealed cutover row in
   `/var/lib/nft/ops/journal.jsonl` whose `gen` matches
   `/var/lib/nft/state/gen.target` and `mode` is `seal`. Equality is
   inclusive (`tip >= floor`). Live sheets under `/etc/nft/floors/` are not
   the durable authority.

3. Base-chain `policy` values in the fold must match
   `/var/lib/nft/ops/prefer.conf` keys shaped `family/table/chain=policy`
   (for example `inet/filter/input=drop` and `inet/filter/output=accept`).
   Surface prefer under `/etc/nft/surface_prefer.conf` is not authority.

4. Abort-window residue under `/var/lib/nft/ops/abort.d/` rematerializes into
   live `/etc/nftables.d/90-local.nft` on every seating pass unless
   `/var/lib/nft/state/cutover.ok` exists as plain `key=value` lines with
   exactly `gen=<target>` (matching `/var/lib/nft/state/gen.target`) and
   `mode=seal`. A matching receipt skips rematerialize; it does **not** mean
   delete the live 90-local slot. That live file must remain present as an
   nftables fragment **without** an abort overlay table (`abort_lab`). A
   comment-only slot is correct. Do **not** paste
   `/app/config/site_standard.conf` (operator memo `key=value` lines) into
   the fragment — that file is not nftables syntax. The abort package itself
   stays forensic.

5. Apply is atomic: flush the loaded ruleset, then load the fold. Additive
   loads that stack passes inflate `rules_applied`. After apply,
   `nft list ruleset` written to `/var/lib/nft/ops/applied.nft` must equal
   the fold (whitespace-normalized).

6. After a successful seating pass, `/var/lib/nft/state/gen.live` must equal
   `/var/lib/nft/state/gen.target` (the sealed cutover generation now live on
   the desk). Stale live markers left behind from earlier tips keep seating
   incomplete even when the fold looks right.

7. Table families: `filter` is `inet`; `nat`, `mangle`, and `raw` are `ip`.
   Roster order is `/etc/nft/roster.list`.

8. Two sequential seating runs must leave byte-identical
   `/output/nft-seat.json`.
