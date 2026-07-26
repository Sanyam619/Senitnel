use crate::types::KernelId;

// The policy file lives at /app/data/policy/handoff.spec and pins
// the kernel adopted by the runner for post-checkpoint work. The
// file format is one key=value per line, blank/# lines skipped.

#[derive(Clone, Debug)]
pub struct Policy {
    pub selected_kernel: KernelId,
    pub authority: String,
}

pub fn read_policy(path: &std::path::Path) -> std::io::Result<Policy> {
    let text = std::fs::read_to_string(path)?;
    let mut selected: Option<KernelId> = None;
    let mut authority: String = String::from("unspecified");
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
                authority = val.trim_matches('"').to_string();
            }
            _ => {}
        }
    }
    let sel = selected.ok_or_else(|| {
        std::io::Error::new(
            std::io::ErrorKind::InvalidData,
            "policy file missing selected_kernel entry",
        )
    })?;
    Ok(Policy { selected_kernel: sel, authority })
}
