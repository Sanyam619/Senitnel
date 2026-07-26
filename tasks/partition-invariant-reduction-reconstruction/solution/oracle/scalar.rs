pub fn wire_f64_bits(v: f64) -> String {
    let bytes = v.to_be_bytes();
    let mut out = String::with_capacity(16);
    for b in bytes {
        out.push_str(&format!("{b:02x}"));
    }
    out
}
