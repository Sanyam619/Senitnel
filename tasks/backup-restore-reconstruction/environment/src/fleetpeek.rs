//! Read-only episode inspector. Does not write recovery outputs.

use std::fs;
use std::path::Path;

fn main() {
    let app = Path::new("/app");
    let eps = app.join("data").join("episodes");
    let mut names: Vec<_> = fs::read_dir(&eps)
        .expect("episodes")
        .filter_map(|e| e.ok())
        .filter(|e| e.path().is_dir())
        .map(|e| e.file_name().to_string_lossy().into_owned())
        .collect();
    names.sort();
    println!("fleetpeek: {} episode export(s)", names.len());
    for n in names {
        let coord = eps.join(&n).join("coordinator.jsonl");
        let lines = fs::read_to_string(&coord).unwrap_or_default();
        let nlines = lines.lines().filter(|l| !l.trim().is_empty()).count();
        let seal = eps.join(&n).join("volume_seal.json");
        let seal_ok = seal.is_file();
        println!(
            "  {n}: coordinator_rows={nlines} volume_seal={}",
            if seal_ok { "present" } else { "missing" }
        );
    }
    println!("fleetpeek: surface inventory complete (read-only)");
}
