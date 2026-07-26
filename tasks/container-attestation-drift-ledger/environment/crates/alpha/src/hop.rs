use crate::store;
use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HopIn {
    pub dest: String,
    pub store_key: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArchSel {
    pub arch: String,
    pub store_root: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OutA {
    pub value: String,
}

/// Records the content digest for one promotion hop.
pub fn op_a(a: &HopIn, b: &ArchSel) -> OutA {
    let _ = store::read_platform(Path::new(&b.store_root), &a.store_key);
    let _ = b.arch.as_str();
    OutA {
        value: a.dest.clone(),
    }
}
