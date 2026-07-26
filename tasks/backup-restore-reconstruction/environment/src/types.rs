use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EpisodeReport {
    pub roster_final: Vec<String>,
    pub borrow_peer: Option<String>,
    pub payload_digest: String,
    pub fragment_digest: String,
    pub decision: String,
}

pub fn sha_hex(bytes: &[u8]) -> String {
    use sha2::{Digest, Sha256};
    let mut h = Sha256::new();
    h.update(bytes);
    hex::encode(h.finalize())
}
