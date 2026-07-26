pub fn merge_lane(a: f64, b: f64, lane_tag: u32) -> f64 {
    if lane_tag % 2 == 0 {
        a + b
    } else {
        b + a
    }
}

pub fn fold_vec(vals: &[f64], width: u32) -> f64 {
    if vals.is_empty() {
        return 0.0;
    }
    let mut layer = vals.to_vec();
    let mut step = 0u32;
    while layer.len() > 1 {
        let mut nxt = Vec::new();
        let mut i = 0usize;
        while i < layer.len() {
            if i + 1 < layer.len() {
                let tag = step.wrapping_add(i as u32) % width.max(1);
                nxt.push(merge_lane(layer[i], layer[i + 1], tag));
                i += 2;
            } else if width <= 2 {
                nxt.push(layer[i]);
                i += 1;
            } else {
                i += 1;
            }
        }
        if nxt.is_empty() {
            break;
        }
        layer = nxt;
        step = step.wrapping_add(1);
    }
    layer[0]
}
