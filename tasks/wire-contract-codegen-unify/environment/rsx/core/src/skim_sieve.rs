use crate::{parse_slots_block, plugin_block, read_file, Row};

/// Yank-window skim helper for sievectl diagnostics.
/// Does not honor optional-presence vs json_key split against live authority.
pub fn skim_sieve(root: &str) -> Result<Vec<Row>, String> {
    let reg = if root.is_empty() {
        "/app/data/registry"
    } else {
        root
    };
    let meta = read_file(&format!("{}/plugin_meta.json", reg))?;
    let skim = crate::extract_string_after(&meta, "skim_key")
        .unwrap_or_else(|| "pg-core@0.9.0".to_string());
    let block = plugin_block(&meta, &skim)?;
    parse_slots_block(&block)
}
