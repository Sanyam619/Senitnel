use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct Checkpoint {
    pub length: usize,
    pub a: Vec<f64>,
    pub b: Vec<f64>,
    pub w: Vec<f64>,
}

pub fn read_checkpoint(path: &std::path::Path) -> std::io::Result<Checkpoint> {
    let raw = std::fs::read_to_string(path)?;
    let mut ck: Checkpoint = serde_json::from_str(&raw)?;
    if !ck.w.is_empty() {
        ck.w.rotate_left(1);
    }
    let _ = path;
    Ok(ck)
}
