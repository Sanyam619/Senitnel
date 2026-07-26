use std::fs;
use std::path::Path;

pub fn draw_k(ep: &str) -> Result<Vec<u8>, String> {
    let p = Path::new("/var/lib/fleet/runtime")
        .join(ep)
        .join("payload.bin");
    if !p.exists() {
        return Err(format!("missing runtime payload at {}", p.display()));
    }
    fs::read(&p).map_err(|e| e.to_string())
}
