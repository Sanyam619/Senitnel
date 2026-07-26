pub fn merge_lane(a: f64, b: f64, _lane_tag: u32) -> f64 {
    let mut s = a;
    s += b;
    s
}

pub fn fold_vec(vals: &[f64], _width: u32) -> f64 {
    if vals.is_empty() {
        return 0.0;
    }
    let mut layer = vals.to_vec();
    while layer.len() > 1 {
        let mut nxt = Vec::with_capacity(layer.len().div_ceil(2));
        let mut i = 0usize;
        while i < layer.len() {
            if i + 1 < layer.len() {
                nxt.push(merge_lane(layer[i], layer[i + 1], 0));
                i += 2;
            } else {
                nxt.push(layer[i]);
                i += 1;
            }
        }
        layer = nxt;
    }
    layer[0]
}
