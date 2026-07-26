use crate::types::*;

pub fn active_ring(led: &Ledger, cos: &CosignerBook, _at_epoch: u64) -> Vec<String> {
    let latest = led
        .rotations
        .last()
        .expect("ceremony ledger has no rotations");
    let now = cos.now_epoch;
    latest
        .members
        .iter()
        .filter(|m| {
            cos.revocations
                .iter()
                .all(|r| &r.cosigner_id != *m || r.revoked_at > now)
        })
        .cloned()
        .collect()
}

pub fn threshold_at(led: &Ledger, _at_epoch: u64) -> u32 {
    led.rotations
        .last()
        .expect("ceremony ledger has no rotations")
        .threshold
}
