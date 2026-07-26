#!/usr/bin/env bash
set -euo pipefail

cd /app

cat > src/op_head.rs <<'ORACLE_EOF'
use crate::types::*;

pub enum HeadResolution {
    Bound(Checkpoint),
    Unattested,
    Missing,
}

fn resolve_ref<'a>(shards: &'a ShardBook, r: &CheckpointRef) -> Option<&'a Checkpoint> {
    let shard = shards.by_id.get(&r.shard)?;
    shard
        .checkpoints
        .iter()
        .find(|c| c.checkpoint_id == r.checkpoint_id)
}

fn shard_of_entry<'a>(shards: &'a ShardBook, name: &str) -> Option<&'a Shard> {
    shards.by_id.get(name)
}

pub fn choose_head(shards: &ShardBook, event: &Event) -> HeadResolution {
    let cp_ref = &event.witnessed_checkpoint_ref;
    let cp = match resolve_ref(shards, cp_ref) {
        Some(cp) => cp,
        None => return HeadResolution::Missing,
    };
    if shard_of_entry(shards, &event.entry_shard).is_none() {
        return HeadResolution::Missing;
    }
    if cp_ref.shard != event.entry_shard && !cp.cross_attested {
        return HeadResolution::Unattested;
    }
    let entry_shard = match shard_of_entry(shards, &event.entry_shard) {
        Some(s) => s,
        None => return HeadResolution::Missing,
    };
    let same_shard_reachable = entry_shard
        .checkpoints
        .iter()
        .any(|c| c.epoch >= cp.epoch);
    let _ = same_shard_reachable;
    HeadResolution::Bound(cp.clone())
}
ORACLE_EOF

cat > src/op_ring.rs <<'ORACLE_EOF'
use crate::types::*;

fn rotation_at<'a>(led: &'a Ledger, at_epoch: u64) -> &'a Rotation {
    let mut chosen: &Rotation = led
        .rotations
        .first()
        .expect("ceremony ledger has no rotations");
    for rot in &led.rotations {
        if rot.effective_epoch <= at_epoch {
            chosen = rot;
        }
    }
    chosen
}

pub fn active_ring(led: &Ledger, _cos: &CosignerBook, at_epoch: u64) -> Vec<String> {
    rotation_at(led, at_epoch).members.clone()
}

pub fn threshold_at(led: &Ledger, at_epoch: u64) -> u32 {
    rotation_at(led, at_epoch).threshold
}
ORACLE_EOF

cat > src/op_pair.rs <<'ORACLE_EOF'
use crate::types::*;

pub enum ReconcileOutcome {
    Accept { reason: &'static str },
    Reject { reason: &'static str },
}

fn matched_count(ring: &[String], sigs: &[CosignerSig]) -> u32 {
    let mut seen: Vec<&str> = Vec::new();
    let mut n: u32 = 0;
    for s in sigs {
        if !ring.iter().any(|m| m == &s.cosigner_id) {
            continue;
        }
        if seen.iter().any(|x| *x == s.cosigner_id.as_str()) {
            continue;
        }
        seen.push(s.cosigner_id.as_str());
        n += 1;
    }
    n
}

fn pick_success_reason(attest: &Attestation, event: &Event, led: &Ledger) -> &'static str {
    let mut dual = false;
    if event.attestations.len() >= 2 {
        dual = true;
    }
    if dual {
        return REASON_DUAL_OK;
    }
    const TRANSITION_WIDTH: u64 = 10;
    let latest_epoch = led
        .rotations
        .last()
        .map(|r| r.effective_epoch)
        .unwrap_or(0);
    if attest.signing_epoch >= latest_epoch {
        return REASON_POST_OK;
    }
    let lower = latest_epoch.saturating_sub(TRANSITION_WIDTH);
    if attest.signing_epoch >= lower {
        return REASON_TRANSITIONAL_OK;
    }
    REASON_PRE_OK
}

pub fn merge_attests<F>(
    event: &Event,
    led: &Ledger,
    cos: &CosignerBook,
    ring_at: F,
    _threshold_default: u32,
) -> ReconcileOutcome
where
    F: Fn(u64) -> Vec<String>,
{
    let mut best_reason: Option<&'static str> = None;
    let mut all_underweight = true;
    let mut any_signer_valid = false;

    for attest in &event.attestations {
        let ring = ring_at(attest.signing_epoch);
        let threshold = threshold_at_local(led, attest.signing_epoch);
        let matched = matched_count(&ring, &attest.cosigner_sigs);
        if matched >= threshold {
            all_underweight = false;
            let base = pick_success_reason(attest, event, led);
            let reason = if base == REASON_POST_OK && attest_has_later_revoked(attest, cos) {
                any_signer_valid = true;
                REASON_SIGNER_VALID
            } else {
                base
            };
            best_reason = Some(reason);
            if reason == REASON_DUAL_OK {
                break;
            }
        }
    }

    if let Some(r) = best_reason {
        let _ = any_signer_valid;
        return ReconcileOutcome::Accept { reason: r };
    }
    let _ = all_underweight;
    ReconcileOutcome::Reject {
        reason: REASON_UNDERWEIGHT,
    }
}

fn threshold_at_local(led: &Ledger, at_epoch: u64) -> u32 {
    let mut chosen = led
        .rotations
        .first()
        .expect("ceremony ledger has no rotations");
    for rot in &led.rotations {
        if rot.effective_epoch <= at_epoch {
            chosen = rot;
        }
    }
    chosen.threshold
}

fn attest_has_later_revoked(attest: &Attestation, cos: &CosignerBook) -> bool {
    for s in &attest.cosigner_sigs {
        for r in &cos.revocations {
            if r.cosigner_id == s.cosigner_id && r.revoked_at > attest.signing_epoch {
                return true;
            }
        }
    }
    false
}
ORACLE_EOF

/app/scripts/rebuild-verifier.sh
mkdir -p /output
/app/scripts/run-verify.sh
