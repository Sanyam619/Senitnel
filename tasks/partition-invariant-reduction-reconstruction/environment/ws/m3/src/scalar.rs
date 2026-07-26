pub fn wire_f64_bits(v: f64) -> String {
    format!("{:016x}", u64::from_le_bytes(v.to_le_bytes()))
}
