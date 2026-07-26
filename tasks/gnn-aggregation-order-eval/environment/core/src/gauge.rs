use crate::braid;

fn degrees(n: usize, edges: &[(u32, u32)]) -> Vec<f32> {
    let mut deg = vec![0.0f32; n];
    for &(u, v) in edges {
        let ui = u as usize;
        let vi = v as usize;
        if ui < n {
            deg[ui] += 1.0;
        }
        if ui != vi && vi < n {
            deg[vi] += 1.0;
        }
    }
    deg
}

fn adj_list(n: usize, edges: &[(u32, u32)]) -> Vec<Vec<usize>> {
    let mut adj = vec![Vec::new(); n];
    for &(u, v) in edges {
        let ui = u as usize;
        let vi = v as usize;
        if ui < n && vi < n {
            adj[ui].push(vi);
            if ui != vi {
                adj[vi].push(ui);
            }
        }
    }
    for i in 0..n {
        adj[i].sort_unstable();
        adj[i].dedup();
        if !adj[i].contains(&i) {
            adj[i].push(i);
            adj[i].sort_unstable();
        }
    }
    adj
}

fn aggregate(vecs: &[Vec<f32>], mode: &str) -> Vec<f32> {
    if vecs.is_empty() {
        return Vec::new();
    }
    let d = vecs[0].len();
    match mode {
        "sum" => {
            let mut out = vec![0.0f32; d];
            for v in vecs {
                for j in 0..d {
                    out[j] += v[j];
                }
            }
            out
        }
        "max" => {
            let mut out = vecs[0].clone();
            for v in &vecs[1..] {
                for j in 0..d {
                    if v[j] > out[j] {
                        out[j] = v[j];
                    }
                }
            }
            out
        }
        "pna" => {
            let n = vecs.len() as f32;
            let mut mn = vec![0.0f32; d];
            let mut mx = vecs[0].clone();
            for v in vecs {
                for j in 0..d {
                    mn[j] += v[j];
                    if v[j] > mx[j] {
                        mx[j] = v[j];
                    }
                }
            }
            for j in 0..d {
                mn[j] = mn[j] / n + mx[j];
            }
            mn
        }
        _ => {
            let n = vecs.len() as f32;
            let mut out = vec![0.0f32; d];
            for v in vecs {
                for j in 0..d {
                    out[j] += v[j];
                }
            }
            for x in out.iter_mut() {
                *x /= n;
            }
            out
        }
    }
}

pub fn message_pass(
    feats: &[Vec<f32>],
    edges: &[(u32, u32)],
    agg: &str,
    pref: &str,
) -> Vec<Vec<f32>> {
    let n = feats.len();
    let deg = degrees(n, edges);
    let seated = braid::braid_n(feats, &deg, pref);
    let adj = adj_list(n, edges);
    let mut out = Vec::with_capacity(n);
    for i in 0..n {
        let vecs: Vec<Vec<f32>> = adj[i].iter().map(|&j| seated[j].clone()).collect();
        out.push(aggregate(&vecs, agg));
    }
    out
}

fn matmul(hs: &[Vec<f32>], weights: &[Vec<f32>]) -> Vec<Vec<f64>> {
    let mut logits = Vec::with_capacity(hs.len());
    for h in hs {
        let mut row = Vec::with_capacity(weights.len());
        for w in weights {
            let mut s = 0.0f64;
            let d = h.len().min(w.len());
            for j in 0..d {
                s += h[j] as f64 * w[j] as f64;
            }
            row.push(s);
        }
        logits.push(row);
    }
    logits
}

fn predict(logits: &[Vec<f64>]) -> Vec<usize> {
    logits
        .iter()
        .map(|row| {
            row.iter()
                .enumerate()
                .max_by(|a, b| a.1.partial_cmp(b.1).unwrap_or(std::cmp::Ordering::Equal))
                .map(|(i, _)| i)
                .unwrap_or(0)
        })
        .collect()
}

fn soft_accuracy(logits: &[Vec<f64>], labels: &[u16]) -> f64 {
    if labels.is_empty() {
        return 0.0;
    }
    let mut total = 0.0;
    for (logit, &lab) in logits.iter().zip(labels.iter()) {
        let m = logit.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
        let exps: Vec<f64> = logit.iter().map(|v| (v - m).exp()).collect();
        let z: f64 = exps.iter().sum();
        let li = lab as usize;
        if li < exps.len() && z > 0.0 {
            total += exps[li] / z;
        }
    }
    total / labels.len() as f64
}

fn macro_f1(yhat: &[usize], labels: &[u16], n_class: usize) -> f64 {
    if n_class == 0 {
        return 0.0;
    }
    let mut scores = Vec::with_capacity(n_class);
    for c in 0..n_class {
        let mut tp = 0.0;
        let mut fp = 0.0;
        let mut fn_ = 0.0;
        for (&a, &b) in yhat.iter().zip(labels.iter()) {
            let b = b as usize;
            if a == c && b == c {
                tp += 1.0;
            } else if a == c && b != c {
                fp += 1.0;
            } else if a != c && b == c {
                fn_ += 1.0;
            }
        }
        let prec = if tp + fp > 0.0 { tp / (tp + fp) } else { 0.0 };
        let rec = if tp + fn_ > 0.0 { tp / (tp + fn_) } else { 0.0 };
        let f1 = if prec + rec > 0.0 {
            2.0 * prec * rec / (prec + rec)
        } else {
            0.0
        };
        scores.push(f1);
    }
    scores.iter().sum::<f64>() / n_class as f64
}

pub fn score_lot(lot: &crate::base::Lot, weights: &[Vec<f32>], agg: &str, pref: &str) -> (f64, f64) {
    let hs = message_pass(&lot.feats, &lot.edges, agg, pref);
    let logits = matmul(&hs, weights);
    let yhat = predict(&logits);
    let n_class = weights.len();
    (
        soft_accuracy(&logits, &lot.labels),
        macro_f1(&yhat, &lot.labels, n_class),
    )
}
