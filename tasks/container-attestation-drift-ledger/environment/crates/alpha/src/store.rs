use serde::Deserialize;
use std::fs;
use std::path::Path;

#[derive(Debug, Deserialize)]
pub struct IndexDoc {
    pub digest: String,
    pub arch: String,
    pub child: String,
}

#[derive(Debug, Deserialize)]
pub struct PlatformDoc {
    pub digest: String,
    pub arch: String,
}

pub fn read_index(root: &Path, key: &str) -> Option<IndexDoc> {
    let p = root.join(key).join("index.json");
    let text = fs::read_to_string(p).ok()?;
    serde_json::from_str(&text).ok()
}

pub fn read_platform(root: &Path, key: &str) -> Option<PlatformDoc> {
    let p = root.join(key).join("platform.json");
    let text = fs::read_to_string(p).ok()?;
    serde_json::from_str(&text).ok()
}
