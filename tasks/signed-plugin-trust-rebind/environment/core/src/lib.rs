pub const DATA_ROOT: &str = "/app/data";
pub const OPS_ROOT: &str = "/app/ops";
pub const CONFIG_ROOT: &str = "/app/config";
pub const CREDENTIALS_DIR: &str = "/app/data/credentials";
pub const SEGMENTS_DIR: &str = "/app/data/signed_segments";

pub fn derive_epoch_key(seed: &[u8], _epoch: u16) -> Vec<u8> {
    seed.to_vec()
}

pub fn derive_frame_key(seed: &[u8], _epoch: u16, _lane: u8, _strand: u8) -> Vec<u8> {
    seed.to_vec()
}

pub fn load_strand() -> u8 {
    0
}
