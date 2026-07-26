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
    let ck: Checkpoint = serde_json::from_str(&raw)?;
    if ck.a.len() != ck.length || ck.b.len() != ck.length || ck.w.len() != ck.length {
        return Err(std::io::Error::new(
            std::io::ErrorKind::InvalidData,
            "checkpoint lane length mismatch",
        ));
    }
    let _ = path;
    Ok(ck)
}
