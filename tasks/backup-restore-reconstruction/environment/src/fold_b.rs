use serde::Deserialize;
use std::fs;
use std::path::Path;

use crate::slot_e::Arms;

#[derive(Debug, Deserialize)]
struct BagA {
    claims: Vec<Node>,
}

#[derive(Debug, Deserialize, Clone)]
struct Node {
    peer: String,
    live: bool,
    sealed: bool,
    ts: u64,
    #[allow(dead_code)]
    token: String,
}

fn take_a(path: &Path) -> Result<Vec<Node>, String> {
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    let cf: BagA = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
    Ok(cf.claims)
}

fn gated(ep: &str, peer: &str) -> bool {
    Path::new("/var/run/fleet/gate")
        .join(ep)
        .join(peer)
        .is_file()
}

pub fn pick_n(ep: &str, pol: &Arms) -> Result<Option<String>, String> {
    let lease_path = Path::new("/var/lib/fleet/leases").join(format!("{ep}.json"));
    let claims = take_a(&lease_path)?;

    if pol.precedence == "seal_first" && pol.borrow_gate == "live_and_clear" {
        let eligible: Vec<Node> = claims
            .into_iter()
            .filter(|c| c.live && !gated(ep, &c.peer))
            .collect();
        if eligible.is_empty() {
            return Ok(None);
        }
        let sealed: Vec<Node> = eligible.iter().filter(|c| c.sealed).cloned().collect();
        let pool = if !sealed.is_empty() { sealed } else { eligible };
        let best = pool.into_iter().min_by_key(|c| c.ts).map(|c| c.peer);
        return Ok(best);
    }

    let mut best: Option<Node> = None;
    for c in claims {
        if !c.live {
            continue;
        }
        match &best {
            None => best = Some(c),
            Some(b) if c.ts > b.ts => best = Some(c),
            _ => {}
        }
    }
    Ok(best.map(|c| c.peer))
}
