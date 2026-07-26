//! Fleet mesh recovery library.

pub mod emit_d;
pub mod fold_b;
pub mod knit_a;
pub mod phase_x;
pub mod phase_y;
pub mod phase_z;
pub mod skim_c;
pub mod skim_w;
pub mod fold_w;
pub mod slot_e;
pub mod types;

use std::path::Path;

use types::EpisodeReport;

pub fn run_all(app: &Path, out: &Path) -> Result<(), String> {
    // fleetd supervisor pidfile gate for reconcile.
    let pid = Path::new("/var/run/fleet/fleetd.pid");
    if !pid.is_file() {
        return Err("fleetd is not running (missing /var/run/fleet/fleetd.pid)".into());
    }

    let eps = app.join("data").join("episodes");
    let pol = phase_z::load_policy(app)?;
    let mut episodes = serde_json::Map::new();
    let mut names: Vec<String> = std::fs::read_dir(&eps)
        .map_err(|e| e.to_string())?
        .filter_map(|e| e.ok())
        .filter(|e| e.path().is_dir())
        .map(|e| e.file_name().to_string_lossy().into_owned())
        .collect();
    names.sort();
    for name in names {
        let dir = eps.join(&name);
        let rep = recover_one(&dir, &name, &pol, out)?;
        episodes.insert(name, serde_json::to_value(rep).map_err(|e| e.to_string())?);
    }
    let root = serde_json::json!({ "episodes": episodes });
    std::fs::create_dir_all(out).map_err(|e| e.to_string())?;
    let path = out.join("reconciliation.json");
    std::fs::write(
        &path,
        serde_json::to_string_pretty(&root).map_err(|e| e.to_string())? + "\n",
    )
    .map_err(|e| e.to_string())?;
    let meta = out.join("meta");
    std::fs::create_dir_all(&meta).map_err(|e| e.to_string())?;
    let stamp = format!(
        "fleetctl:{}:{}:{}\n",
        pol.precedence, pol.borrow_gate, pol.fragment_order
    );
    std::fs::write(meta.join("run.stamp"), stamp).map_err(|e| e.to_string())?;
    Ok(())
}

fn recover_one(
    dir: &Path,
    name: &str,
    pol: &slot_e::Arms,
    out: &Path,
) -> Result<EpisodeReport, String> {
    let roster = phase_x::roster_for(dir)?;
    let peer = phase_x::peer_for(name, pol)?;
    let payload = phase_y::payload_for(name)?;
    let frag = phase_y::frag_for(dir, pol)?;
    let decision = phase_z::label_for(name, &roster, peer.as_deref(), pol);

    let dest = out.join("restored").join(name);
    std::fs::create_dir_all(&dest).map_err(|e| e.to_string())?;
    std::fs::write(dest.join("payload.bin"), &payload).map_err(|e| e.to_string())?;
    std::fs::write(dest.join("fragments.bin"), &frag).map_err(|e| e.to_string())?;
    let local = serde_json::json!({
        "episode": name,
        "roster_final": roster,
        "borrow_peer": peer,
        "decision": decision,
    });
    std::fs::write(
        dest.join("report.json"),
        serde_json::to_string_pretty(&local).map_err(|e| e.to_string())? + "\n",
    )
    .map_err(|e| e.to_string())?;

    Ok(EpisodeReport {
        roster_final: roster,
        borrow_peer: peer,
        payload_digest: types::sha_hex(&payload),
        fragment_digest: types::sha_hex(&frag),
        decision,
    })
}
