WireGuard edge handoff lab (/opt/wghandoff)

Fleet operators rotate allowed peer rosters on edge nodes through numbered
epochs. Each rotation promotes a new member set; peers that no longer appear
in the target epoch must leave the live tunnel. A peer that appears in both
the prior epoch and the target epoch is a carry-forward and must remain.

Authority chain (see also data/policy.toml [cutover]):
  epoch_authority = manifest   — target_epoch is the cutover destination
  roster_source = epoch_table  — member ids for an epoch come from that row
  staging_mode = replace       — wire roster is replaced, not merged with queue
  allow_cidr_reuse = true      — AllowedIPs from retired epochs may be reused

Bundle layout under data/scenarios/<node_id>/:
  manifest.json     — desired cutover epoch (target_epoch)
  epoch_table.json  — historical roster rows keyed by epoch plus ledger counter
  live_state.json   — on-wire snapshot: epoch, member_ids, retired_ids
  pending.json      — automation queue left by the last staging pass (may lag)

bundle_index.json lists every lab node and its target_epoch. Operator scripts
under scripts/ mutate live_state.json and epoch_table.json inside each bundle.
bin/reconcile walks all bundles, runs those scripts, validates membership, and
writes handoff_report.json. Field semantics for the report are documented in
cmd/reconcile/main.go.
