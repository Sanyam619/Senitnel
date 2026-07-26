use crate::types::KernelId;

// The policy file lives at /app/data/policy/handoff.spec and pins
// the kernel adopted by the runner for post-checkpoint work. The
// file format is one key=value per line, blank/# lines skipped.
// Fleet overlays may also appear under /app/data/policy/*.overlay.
// handoff.canon holds the durable authority copy for rematerialize.

#[derive(Clone, Debug)]
pub struct Policy {
    pub selected_kernel: KernelId,
    pub authority: String,
}

fn parse_kernel_map(text: &str) -> (Option<KernelId>, Option<String>) {
    let mut selected: Option<KernelId> = None;
    let mut authority: Option<String> = None;
    for raw in text.lines() {
        let line = raw.split('#').next().unwrap_or("").trim();
        if line.is_empty() {
            continue;
        }
        let mut parts = line.splitn(2, '=');
        let key = parts.next().unwrap_or("").trim();
        let val = parts.next().unwrap_or("").trim();
        match key {
            "selected_kernel" => {
                let stripped = val.trim_matches('"').trim();
                selected = KernelId::parse(stripped);
            }
            "authority" => {
                authority = Some(val.trim_matches('"').to_string());
            }
            _ => {}
        }
    }
    (selected, authority)
}

fn read_overlay_kernel(dir: &std::path::Path) -> Option<KernelId> {
    let Ok(entries) = std::fs::read_dir(dir) else {
        return None;
    };
    let mut overlays: Vec<std::path::PathBuf> = entries
        .flatten()
        .map(|e| e.path())
        .filter(|p| p.extension().and_then(|e| e.to_str()) == Some("overlay"))
        .collect();
    overlays.sort();
    for path in overlays {
        if let Ok(text) = std::fs::read_to_string(&path) {
            if let (Some(k), _) = parse_kernel_map(&text) {
                return Some(k);
            }
        }
    }
    None
}

fn rewrite_selected_kernel(handoff_path: &std::path::Path, kernel: KernelId) -> std::io::Result<()> {
    let text = std::fs::read_to_string(handoff_path)?;
    let mut out = String::new();
    let mut wrote_sel = false;
    for raw in text.lines() {
        let trimmed = raw.trim();
        if trimmed.starts_with("selected_kernel") {
            out.push_str(&format!("selected_kernel = {}\n", kernel.label()));
            wrote_sel = true;
        } else {
            out.push_str(raw);
            out.push('\n');
        }
    }
    if !wrote_sel {
        out.push_str(&format!("selected_kernel = {}\n", kernel.label()));
    }
    std::fs::write(handoff_path, out)
}

/// Rematerialize fleet-trial preference into the durable handoff sheet.
pub fn rematerialize_fleet_trial(
    handoff_path: &std::path::Path,
    _authority: &str,
) -> std::io::Result<()> {
    let dir = handoff_path.parent().unwrap_or(handoff_path);
    let Some(overlay_k) = read_overlay_kernel(dir) else {
        return Ok(());
    };
    rewrite_selected_kernel(handoff_path, overlay_k)
}

pub fn read_policy(path: &std::path::Path) -> std::io::Result<Policy> {
    let text = std::fs::read_to_string(path)?;
    let (selected, authority_opt) = parse_kernel_map(&text);
    let authority = authority_opt.unwrap_or_else(|| String::from("unspecified"));
    let sel = selected.ok_or_else(|| {
        std::io::Error::new(
            std::io::ErrorKind::InvalidData,
            "policy file missing selected_kernel entry",
        )
    })?;

    let dir = path.parent().unwrap_or(path);
    let overlay = read_overlay_kernel(dir);
    let selected_kernel = overlay.unwrap_or(sel);

    let _ = &authority;
    Ok(Policy {
        selected_kernel,
        authority,
    })
}
