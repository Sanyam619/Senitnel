mod sieve_b;
mod skim_sieve;

pub use sieve_b::sieve_b;
pub use skim_sieve::skim_sieve;

#[derive(Clone, Debug)]
pub struct Row {
    pub slot: String,
    pub tag: i64,
    pub kind: String,
    pub json_key: String,
}

impl Row {
    pub fn to_json(&self) -> String {
        format!(
            "{{\"slot\":{},\"tag\":{},\"kind\":{},\"json_key\":{}}}",
            json_str(&self.slot),
            self.tag,
            json_str(&self.kind),
            json_str(&self.json_key)
        )
    }
}

pub fn rows_to_json(rows: &[Row]) -> String {
    let body: Vec<String> = rows.iter().map(|r| r.to_json()).collect();
    format!("[{}]", body.join(","))
}

fn json_str(s: &str) -> String {
    let mut out = String::from("\"");
    for ch in s.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            _ => out.push(ch),
        }
    }
    out.push('"');
    out
}

pub fn read_file(path: &str) -> Result<String, String> {
    std::fs::read_to_string(path).map_err(|e| e.to_string())
}

/// Extract a JSON string value for key after a `"key"` occurrence.
pub fn extract_string_after(hay: &str, key: &str) -> Option<String> {
    let pat = format!("\"{}\"", key);
    let idx = hay.find(&pat)?;
    let rest = &hay[idx + pat.len()..];
    let colon = rest.find(':')?;
    let mut r = rest[colon + 1..].trim_start();
    if !r.starts_with('"') {
        return None;
    }
    r = &r[1..];
    let mut out = String::new();
    let mut chars = r.chars();
    while let Some(c) = chars.next() {
        if c == '\\' {
            if let Some(n) = chars.next() {
                out.push(n);
            }
            continue;
        }
        if c == '"' {
            break;
        }
        out.push(c);
    }
    Some(out)
}

pub fn extract_i64_after(hay: &str, key: &str) -> Option<i64> {
    let pat = format!("\"{}\"", key);
    let idx = hay.find(&pat)?;
    let rest = &hay[idx + pat.len()..];
    let colon = rest.find(':')?;
    let r = rest[colon + 1..].trim_start();
    let num: String = r
        .chars()
        .take_while(|c| c.is_ascii_digit() || *c == '-')
        .collect();
    num.parse().ok()
}

pub fn parse_slots_block(block: &str) -> Result<Vec<Row>, String> {
    let mut rows = Vec::new();
    let mut search = block;
    while let Some(pos) = search.find("\"slot\"") {
        let chunk = &search[pos..];
        let end = chunk.find('}').unwrap_or(chunk.len());
        let obj = &chunk[..end];
        let slot = extract_string_after(obj, "slot").ok_or("missing slot")?;
        let tag = extract_i64_after(obj, "tag").ok_or("missing tag")?;
        let kind = extract_string_after(obj, "kind").ok_or("missing kind")?;
        let json_key = extract_string_after(obj, "json_key").ok_or("missing json_key")?;
        rows.push(Row {
            slot,
            tag,
            kind,
            json_key,
        });
        search = &chunk[end..];
    }
    Ok(rows)
}

pub fn plugin_block(meta: &str, key: &str) -> Result<String, String> {
    let needle = format!("\"{}\"", key);
    let idx = meta
        .find(&needle)
        .ok_or_else(|| format!("missing plugin {}", key))?;
    let rest = &meta[idx..];
    let slots_idx = rest
        .find("\"slots\"")
        .ok_or("missing slots")?;
    let after = &rest[slots_idx..];
    let start = after
        .find('[')
        .ok_or("missing slots array")?;
    let mut depth = 0i32;
    let bytes = after.as_bytes();
    let mut end = start;
    for i in start..after.len() {
        match bytes[i] {
            b'[' => depth += 1,
            b']' => {
                depth -= 1;
                if depth == 0 {
                    end = i + 1;
                    break;
                }
            }
            _ => {}
        }
    }
    Ok(after[start..end].to_string())
}
