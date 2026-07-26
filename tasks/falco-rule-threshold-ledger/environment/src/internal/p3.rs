use crate::internal::tape::{BatchEvent, RuleDoc};
use crate::mk8;

pub fn label_pairs(ev: &BatchEvent) -> Vec<(String, String)> {
    ev.labels.iter().map(|(k, v)| (k.clone(), v.clone())).collect()
}

pub fn label_refs<'a>(pairs: &'a [(String, String)]) -> Vec<(&'a str, &'a str)> {
    pairs.iter().map(|(k, v)| (k.as_str(), v.as_str())).collect()
}

pub fn scope_ok(cid: &str, prefix: &str, labels: &[(&str, &str)]) -> bool {
    mk8::N8_mask(cid, prefix, labels)
}

pub fn matching_rules<'a>(
    syscall: &str,
    cid: &str,
    labels: &[(String, String)],
    rules: &'a [RuleDoc],
    floor: i32,
) -> Vec<&'a RuleDoc> {
    let refs = label_refs(labels);
    rules
        .iter()
        .filter(|r| r.syscall == syscall && r.priority > floor)
        .filter(|r| scope_ok(cid, &r.scope_prefix, &refs))
        .collect()
}
