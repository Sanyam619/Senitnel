pub fn N8_mask(cid: &str, prefix: &str, labels: &[(&str, &str)]) -> bool {
    cid.starts_with(prefix)
        && (labels.is_empty() || labels.iter().all(|(k, v)| *k == "env" && *v == "prod"))
}
