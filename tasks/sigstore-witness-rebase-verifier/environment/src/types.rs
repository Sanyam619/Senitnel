use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Cosigner {
    pub cosigner_id: String,
    pub public_key: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Revocation {
    pub cosigner_id: String,
    pub revoked_at: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CosignerBook {
    pub now_epoch: u64,
    pub cosigners: Vec<Cosigner>,
    pub revocations: Vec<Revocation>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Rotation {
    pub effective_epoch: u64,
    pub members: Vec<String>,
    pub threshold: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Ledger {
    pub rotations: Vec<Rotation>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Checkpoint {
    pub checkpoint_id: String,
    pub shard: String,
    pub epoch: u64,
    pub tree_size: u64,
    pub root_hash: String,
    #[serde(default)]
    pub cross_attested: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Shard {
    pub shard_id: String,
    pub checkpoints: Vec<Checkpoint>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ShardBook {
    pub by_id: std::collections::BTreeMap<String, Shard>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CosignerSig {
    pub cosigner_id: String,
    pub sig: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Attestation {
    pub signing_epoch: u64,
    pub cosigner_sigs: Vec<CosignerSig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CheckpointRef {
    pub shard: String,
    pub checkpoint_id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Event {
    pub event_id: String,
    pub entry_shard: String,
    pub entry_index: u64,
    pub witnessed_checkpoint_ref: CheckpointRef,
    pub attestations: Vec<Attestation>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StateNow {
    pub now_epoch: u64,
}

pub const REASON_PRE_OK: &str = "pre_rotation_ok";
pub const REASON_TRANSITIONAL_OK: &str = "transitional_ok";
pub const REASON_POST_OK: &str = "post_rotation_ok";
pub const REASON_DUAL_OK: &str = "dual_attest_ok";
pub const REASON_SIGNER_VALID: &str = "signer_valid_at_time";
pub const REASON_UNDERWEIGHT: &str = "threshold_shortfall";
pub const REASON_CROSS_SHARD: &str = "cross_shard_unattested";
pub const REASON_STALE_HEAD: &str = "checkpoint_unbound";

pub const ACCEPT_REASONS: &[&str] = &[
    REASON_PRE_OK,
    REASON_TRANSITIONAL_OK,
    REASON_POST_OK,
    REASON_DUAL_OK,
    REASON_SIGNER_VALID,
];

pub const REJECT_REASONS: &[&str] = &[
    REASON_UNDERWEIGHT,
    REASON_CROSS_SHARD,
    REASON_STALE_HEAD,
];
