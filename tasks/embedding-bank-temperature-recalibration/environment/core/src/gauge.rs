use crate::base::Lot;
use crate::braid::braid_k;

pub fn d2(a: &[f32], b: &[f32]) -> f64 {
    let mut s = 0f64;
    for i in 0..a.len().min(b.len()) {
        let d = a[i] as f64 - b[i] as f64;
        s += d * d;
    }
    s
}

fn d2c(a: &[f32], c: &[f64]) -> f64 {
    let mut s = 0f64;
    for i in 0..a.len().min(c.len()) {
        let d = a[i] as f64 - c[i];
        s += d * d;
    }
    s
}

pub fn hits_at(qs: &[Vec<f32>], qt: &[u16], lot: &Lot, tau: f64, k: usize) -> usize {
    if qs.is_empty() || lot.rows.is_empty() {
        return 0;
    }
    let mut hits = 0usize;
    for span in braid_k(qs.len(), 32) {
        for qi in span {
            let q = &qs[qi];
            let mut scored: Vec<(f64, usize)> = lot
                .rows
                .iter()
                .enumerate()
                .map(|(ri, row)| (-d2(q, row) + tau * lot.lw[ri] as f64, ri))
                .collect();
            scored.sort_by(|x, y| y.0.total_cmp(&x.0).then(x.1.cmp(&y.1)));
            let top = &scored[..k.min(scored.len())];
            if top.iter().any(|&(_, ri)| lot.tags[ri] == qt[qi]) {
                hits += 1;
            }
        }
    }
    hits
}

pub fn r_at(qs: &[Vec<f32>], qt: &[u16], lot: &Lot, tau: f64, k: usize) -> f64 {
    if qs.is_empty() {
        return 0.0;
    }
    hits_at(qs, qt, lot, tau, k) as f64 / qs.len() as f64
}

pub fn agree(qs: &[Vec<f32>], qt: &[u16], lot: &Lot, tau: f64) -> f64 {
    if qs.is_empty() || lot.rows.is_empty() {
        return 0.0;
    }
    let dim = lot.rows[0].len();
    let mut kinds: Vec<u16> = lot.tags.clone();
    kinds.sort_unstable();
    kinds.dedup();
    if kinds.len() < 2 {
        return 0.0;
    }
    let total = lot.rows.len() as f64;
    let mut cores: Vec<Vec<f64>> = Vec::with_capacity(kinds.len());
    let mut lp: Vec<f64> = Vec::with_capacity(kinds.len());
    for &kind in &kinds {
        let mut acc = vec![0f64; dim];
        let mut cnt = 0f64;
        for (ri, row) in lot.rows.iter().enumerate() {
            if lot.tags[ri] == kind {
                for (j, v) in row.iter().enumerate() {
                    acc[j] += *v as f64;
                }
                cnt += 1.0;
            }
        }
        for v in acc.iter_mut() {
            *v /= cnt;
        }
        lp.push((cnt / total).ln());
        cores.push(acc);
    }
    let mut asg: Vec<usize> = Vec::with_capacity(qs.len());
    for q in qs {
        let mut best = 0usize;
        let mut best_s = f64::NEG_INFINITY;
        for (ci, core) in cores.iter().enumerate() {
            let s = -d2c(q, core) + tau * lp[ci];
            if s > best_s {
                best_s = s;
                best = ci;
            }
        }
        asg.push(best);
    }
    let mut truth: Vec<u16> = qt.to_vec();
    truth.sort_unstable();
    truth.dedup();
    let nq = qs.len() as f64;
    let mut joint = vec![vec![0f64; kinds.len()]; truth.len()];
    for (qi, &a) in asg.iter().enumerate() {
        let ti = truth.iter().position(|&t| t == qt[qi]).unwrap_or(0);
        joint[ti][a] += 1.0;
    }
    let mut pt = vec![0f64; truth.len()];
    let mut pa = vec![0f64; kinds.len()];
    for (ti, row) in joint.iter().enumerate() {
        for (ai, &c) in row.iter().enumerate() {
            pt[ti] += c / nq;
            pa[ai] += c / nq;
        }
    }
    let mut mi = 0f64;
    for (ti, row) in joint.iter().enumerate() {
        for (ai, &c) in row.iter().enumerate() {
            let p = c / nq;
            if p > 0.0 && pt[ti] > 0.0 && pa[ai] > 0.0 {
                mi += p * (p / (pt[ti] * pa[ai])).ln();
            }
        }
    }
    let ht: f64 = pt.iter().filter(|&&p| p > 0.0).map(|&p| -p * p.ln()).sum();
    let ha: f64 = pa.iter().filter(|&&p| p > 0.0).map(|&p| -p * p.ln()).sum();
    if ht <= 0.0 || ha <= 0.0 {
        return 0.0;
    }
    mi / (ht * ha).sqrt()
}
