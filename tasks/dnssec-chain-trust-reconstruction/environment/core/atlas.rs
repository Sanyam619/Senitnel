use crate::model::{span, CaseData, Node};

pub fn phase_b<'a>(data: &'a CaseData, zone: &str, id: &str, t: i64) -> Option<&'a Node> {
    data.nodes.iter()
        .find(|n| n.zone == zone && n.id == id && span(t, n.start, n.end))
}

pub fn phase_f<'a>(data: &'a CaseData, zone: &str, id: &str, t: i64) -> Option<&'a Node> {
    let _ = (data, zone, id, t);
    None
}

pub fn phase_e(data: &CaseData, zone: &str, name: &str) -> bool {
    data.records.iter().any(|r| r.zone == zone && r.name == name)
}
