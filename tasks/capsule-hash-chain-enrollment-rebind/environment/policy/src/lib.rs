pub mod gate_r;
pub mod skim_pol;

/// Input row for one policy evaluation.
pub struct RowR {
    pub id: String,
    pub claim: i64,
    pub marks: Vec<String>,
    pub lo: i64,
    pub hi: i64,
}

/// Result slot carrying the policy code.
///
/// code values: 0 = clear, 1 = hard block, 2 = window block.
pub struct SlotR {
    pub code: i32,
}

impl SlotR {
    pub fn new() -> SlotR {
        SlotR { code: 0 }
    }
}

impl Default for SlotR {
    fn default() -> Self {
        SlotR::new()
    }
}
