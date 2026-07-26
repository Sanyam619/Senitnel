use crate::types::*;

pub enum ReconcileOutcome {
    Accept { reason: &'static str },
    Reject { reason: &'static str },
}

pub fn merge_attests<F>(
    event: &Event,
    _led: &Ledger,
    cos: &CosignerBook,
    ring_at: F,
    threshold: u32,
) -> ReconcileOutcome
where
    F: Fn(u64) -> Vec<String>,
{
    let now_ring = ring_at(cos.now_epoch);
    let mut totals: usize = 0;
    for attest in &event.attestations {
        let matched = attest
            .cosigner_sigs
            .iter()
            .filter(|s| now_ring.contains(&s.cosigner_id))
            .count();
        if (matched as u32) < threshold {
            return ReconcileOutcome::Reject {
                reason: REASON_UNDERWEIGHT,
            };
        }
        totals += matched;
    }
    let _ = totals;
    ReconcileOutcome::Accept {
        reason: if event.attestations.len() >= 2 {
            REASON_DUAL_OK
        } else {
            REASON_POST_OK
        },
    }
}
