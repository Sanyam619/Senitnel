Reconciliation Contract
=======================

For every episode directory `data/episodes/<name>/` you should produce
one entry under `episodes.<name>` in the aggregate reconciliation
output. Each entry describes four decisions and one bookkeeping value
about the file handle the episode is centered on.

Focused file handle
-------------------
Every episode is centered on the COPY's source file handle (the
`source_fh` field of `copy_intent.rec`). All four decisions describe
what happens to state anchored at that handle. Emit its 32-character
lowercase hex representation as `focused_fh_hex`.

Decisions
---------
1. `delegation_final_state` — the final resting state of the write
   delegation on the focused handle, from the point of view of the
   COPY-issuing client (this is `client_b` in every episode).
     - `held`             delegation is still valid post-reconciliation
     - `downgraded_share` delegation was downgraded (conflict resolution)
     - `released`         delegation was lost (grace window closed
                          without reclaim, source handle now stale)

2. `copy_resolution` — what should happen to the in-flight COPY:
     - `completed`   the COPY was already fully durable on the server
                     before the reboot; no re-emission is required
     - `invalidated` the source handle no longer refers to the object
                     the copy was reading (a rename beat the copy)
     - `restarted`   the COPY should be re-initiated from scratch
                     because the source-side state is no longer live
     - `resumed`     the COPY can pick up where it left off

3. `rename_authority` — what happens to any RENAME the client A log
   recorded on the focused handle:
     - `applied`     the rename is materialised in the final namespace
     - `deferred`    the rename cannot take effect (its supporting
                     delegation is no longer live)
     - `not_present` no rename appears in either journal

4. `stateid_seq_next` — a monotonic integer strictly greater than
   every `stateid_seq` observed anywhere in the episode's server or
   client logs (including SEQ_TICK ticks). This is what the reclaim
   sequence would resume from on the next open.

Priority
--------
The reclaim journal, per-client stateid sequence, and COPY intent
record are three independent state sources. In many episodes they
agree; in some they disagree and a specific ordering resolves it.
That ordering is what makes the outcome different across episodes
even when the individual fields look similar.

Output shape
------------
Aggregate to `/output/reconciliation.json` as a single JSON object:

{
  "episodes": {
    "<name>": {
      "delegation_final_state": "...",
      "copy_resolution": "...",
      "rename_authority": "...",
      "stateid_seq_next": <int>,
      "focused_fh_hex": "<32 lowercase hex chars>"
    },
    ...
  }
}

Every episode present under `data/episodes/` must be reported.
