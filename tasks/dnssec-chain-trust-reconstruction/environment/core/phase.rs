use crate::model::{span, CaseData, Mark, Query};

pub fn phase_a(data: &CaseData, q: &Query) -> Vec<Mark> {
    let mut out: Vec<Mark> = data.marks.iter()
        .filter(|m| m.name == q.name && span(q.instant, m.start, m.end))
        .cloned()
        .collect();
    out.sort_by(|a, b| a.label.cmp(&b.label));
    out
}
