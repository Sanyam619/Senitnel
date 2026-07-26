use m3::types::{LayoutSpec, Segment};
use std::path::Path;

pub fn read_layout(path: &Path) -> std::io::Result<LayoutSpec> {
    let raw = std::fs::read_to_string(path)?;
    let mut name = String::new();
    let mut ranks = 0u32;
    let mut overlap = 0u32;
    let mut segments: Vec<Segment> = Vec::new();
    for line in raw.lines() {
        let line = line.trim();
        if line.starts_with("name =") {
            name = line.split('"').nth(1).unwrap_or("").to_string();
        } else if line.starts_with("ranks =") {
            ranks = line.split('=').nth(1).unwrap().trim().parse().unwrap_or(0);
        } else if line.starts_with("overlap =") {
            overlap = line.split('=').nth(1).unwrap().trim().parse().unwrap_or(0);
        } else if line.contains("rank =") {
            let rank: u32 = line.split("rank =").nth(1).unwrap().split(',').next().unwrap().trim().parse().unwrap();
            let lo: usize = line.split("lo =").nth(1).unwrap().split(',').next().unwrap().trim().parse().unwrap();
            let hi: usize = line.split("hi =").nth(1).unwrap().split('}').next().unwrap().trim().parse().unwrap();
            segments.push(Segment { rank, lo, hi });
        }
    }
    segments.sort_by_key(|s| s.rank);
    Ok(LayoutSpec {
        name,
        ranks,
        overlap,
        segments,
    })
}
