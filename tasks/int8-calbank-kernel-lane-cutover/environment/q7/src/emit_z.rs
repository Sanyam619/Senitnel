use serde::Serialize;
use std::fs;
use std::io;
use std::path::Path;

#[derive(Serialize)]
pub struct Row {
    pub id: String,
    pub lane: String,
    pub mode: String,
    pub top1: f64,
}

#[derive(Serialize)]
pub struct Ledger {
    pub version: u32,
    pub bank_epoch: u32,
    pub scenarios: Vec<Row>,
}

pub fn emit_z(path: &Path, bank_epoch: u32, scenarios: Vec<Row>) -> io::Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    let ledger = Ledger {
        version: 1,
        bank_epoch,
        scenarios,
    };
    let text =
        serde_json::to_string_pretty(&ledger).map_err(|e| io::Error::new(io::ErrorKind::Other, e))?;
    fs::write(path, text)?;
    Ok(())
}
