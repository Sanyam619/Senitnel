use crate::internal::tape::RuleDoc;
use crate::mk3;

pub fn pick_priority(a: i32, b: i32) -> i32 {
    mk3::W3_pick(a, b)
}

pub fn pick_rule<'a>(candidates: &[&'a RuleDoc]) -> Option<&'a RuleDoc> {
    if candidates.is_empty() {
        return None;
    }
    let mut best = candidates[0];
    for cand in &candidates[1..] {
        let pri = pick_priority(cand.priority, best.priority);
        if pri > best.priority || (pri == cand.priority && cand.priority > best.priority) {
            best = cand;
        } else if cand.priority == best.priority && cand.name > best.name {
            best = cand;
        }
    }
    Some(best)
}
