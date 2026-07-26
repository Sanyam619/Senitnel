pub fn reduce_chunks(values: &[f64], chunk_size: usize) -> f64 {
    if values.is_empty() {
        return 0.0;
    }
    let step = chunk_size.max(1);
    let mut acc = 0.0f64;
    let mut i = 0usize;
    while i < values.len() {
        let end = (i + step).min(values.len());
        let mut local = 0.0f64;
        let mut corr = 0.0f64;
        for v in &values[i..end] {
            let y = *v - corr;
            let t = local + y;
            corr = (t - local) - y;
            local = t;
        }
        acc = acc + local;
        i = end;
    }
    acc
}

pub fn compensated_dot(a: &[f64], b: &[f64]) -> f64 {
    let mut sum = 0.0f64;
    let mut corr = 0.0f64;
    for (x, y) in a.iter().zip(b.iter()) {
        let prod = *x * *y;
        let t = sum + (prod - corr);
        corr = (t - sum) - (prod - corr);
        sum = t;
    }
    sum
}

pub fn running_mean(values: &[f64]) -> f64 {
    let mut mean = 0.0f64;
    for (k, v) in values.iter().enumerate() {
        mean += (*v - mean) / ((k + 1) as f64);
    }
    mean
}

pub fn chunk_stability_delta(values: &[f64], probes: &[usize]) -> f64 {
    if probes.is_empty() {
        return 0.0;
    }
    let mut lo = f64::INFINITY;
    let mut hi = f64::NEG_INFINITY;
    for &p in probes {
        let v = reduce_chunks(values, p);
        if v < lo {
            lo = v;
        }
        if v > hi {
            hi = v;
        }
    }
    let scale = hi.abs().max(lo.abs()).max(1e-30);
    (hi - lo).abs() / scale
}
