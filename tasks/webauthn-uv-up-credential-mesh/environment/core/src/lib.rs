use sha2::{Digest, Sha256};

pub const DATA_ROOT: &str = "/app/data";
pub const OPS_ROOT: &str = "/app/ops";
pub const CONFIG_ROOT: &str = "/app/config";
pub const CREDENTIALS_DIR: &str = "/app/data/credentials";
pub const SEGMENTS_DIR: &str = "/app/data/signed_segments";
pub const CEREMONY_ETC: &str = "/etc/ceremony";
pub const CEREMONY_VAR: &str = "/var/lib/ceremony";

pub fn derive_epoch_key(seed: &[u8], epoch: u16) -> Vec<u8> {
    let mut h = Sha256::new();
    h.update(b"wauv.v1\0");
    h.update(seed);
    h.update(&epoch.to_be_bytes());
    h.finalize().to_vec()
}
