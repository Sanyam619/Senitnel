#[derive(Clone, Debug)]
pub struct Segment {
    pub rank: u32,
    pub lo: usize,
    pub hi: usize,
}

#[derive(Clone, Debug)]
pub struct LayoutSpec {
    pub name: String,
    pub ranks: u32,
    pub overlap: u32,
    pub segments: Vec<Segment>,
}

#[derive(Clone, Debug, serde::Serialize)]
pub struct MetricBundle {
    pub sum_w_bits: String,
    pub dot_ab_bits: String,
    pub l2_sq_bits: String,
}
