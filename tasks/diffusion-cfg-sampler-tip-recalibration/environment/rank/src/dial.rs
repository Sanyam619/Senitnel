use std::path::Path;

pub struct DialCfg {
    pub stride: usize,
    pub group: String,
}

pub fn dial_v(ops: &Path) -> DialCfg {
    let mut cfg = DialCfg {
        stride: 8,
        group: "cell".to_string(),
    };
    let Ok(text) = std::fs::read_to_string(ops.join("trace_pref.toml")) else {
        return cfg;
    };
    for line in text.lines() {
        let line = line.trim();
        if let Some(rest) = line.strip_prefix("stride") {
            let rest = rest.trim_start();
            if let Some(rest) = rest.strip_prefix('=') {
                if let Ok(v) = rest.trim().parse::<usize>() {
                    if v > 0 {
                        cfg.stride = v;
                    }
                }
            }
        } else if let Some(rest) = line.strip_prefix("group") {
            let rest = rest.trim_start();
            if let Some(rest) = rest.strip_prefix('=') {
                cfg.group = rest.trim().trim_matches('"').to_string();
            }
        }
    }
    cfg
}
