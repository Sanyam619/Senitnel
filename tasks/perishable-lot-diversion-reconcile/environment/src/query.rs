use std::{fs, path::Path};

use crate::{io, state::Runtime};

pub fn point(root: &Path, args: &[String]) -> Result<(), String> {
    let lane = flag(args, "--lane")?;
    let lot = flag(args, "--lot")?;
    let ts: u64 = flag(args, "--ts")?
        .parse()
        .map_err(|_| "bad ts".to_string())?;
    let rt = Runtime::load(root)?;
    for s in io::shipments(root)? {
        if s.lane == lane
            && s.lot == lot
            && s.ts <= ts
            && s.batch <= rt.active_batch
            && !rt.hold_lots.contains(&s.lot)
        {
            println!(
                "{{\"found\":true,\"lane\":\"{}\",\"lot\":\"{}\",\"destination\":\"{}\",\"ts\":{},\"temp_max\":{}}}",
                s.lane, s.lot, s.dest, s.ts, s.temp
            );
            return Ok(());
        }
    }
    println!("{{\"found\":false,\"lane\":\"{}\",\"lot\":\"{}\"}}", lane, lot);
    Ok(())
}

pub fn scan(root: &Path, args: &[String]) -> Result<(), String> {
    let lane = flag(args, "--lane")?;
    let lo = flag(args, "--lo")?;
    let hi = flag(args, "--hi")?;
    let _ts: u64 = flag(args, "--ts")?
        .parse()
        .map_err(|_| "bad ts".to_string())?;
    // Range scans are served from the sealed sidecar, not the live ledger join.
    let raw = fs::read_to_string(root.join("sidecars").join(format!("{lane}.idx")))
        .map_err(|e| format!("read sidecar {lane}: {e}"))?;
    let lots = sidecar_lots(&raw)?;
    let mut hits = Vec::new();
    for lot in lots {
        if lot >= lo && lot <= hi {
            hits.push(lot);
        }
    }
    hits.sort();
    let body = hits
        .iter()
        .map(|lot| format!("{{\"lot\":\"{lot}\"}}"))
        .collect::<Vec<_>>()
        .join(",");
    println!("{{\"hits\":[{body}]}}");
    Ok(())
}

fn sidecar_lots(raw: &str) -> Result<Vec<String>, String> {
    let key = "\"lots\"";
    let pos = raw.find(key).ok_or_else(|| "missing lots".to_string())?;
    let after = &raw[pos + key.len()..];
    let start = after.find('[').ok_or_else(|| "bad lots".to_string())?;
    let end = after[start..]
        .find(']')
        .ok_or_else(|| "bad lots".to_string())?;
    Ok(after[start + 1..start + end]
        .split(',')
        .map(|s| s.trim().trim_matches('"').to_string())
        .filter(|s| !s.is_empty())
        .collect())
}

fn flag(args: &[String], key: &str) -> Result<String, String> {
    for win in args.windows(2) {
        if win[0] == key {
            return Ok(win[1].clone());
        }
    }
    Err(format!("missing {key}"))
}
