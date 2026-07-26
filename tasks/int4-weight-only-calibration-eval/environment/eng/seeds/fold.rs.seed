//! Four-bit weight round trip.

/// Extent of one group inside a run of `len` entries.
pub fn span(group: usize, len: usize) -> usize {
    if group == 0 || group > len || len % group != 0 {
        len
    } else {
        group
    }
}

fn step_of(top: f64) -> f64 {
    if top > 0.0 {
        top / 7.0
    } else {
        1.0
    }
}

fn clamp(q: f64) -> f64 {
    if q > 7.0 {
        7.0
    } else if q < -8.0 {
        -8.0
    } else {
        q
    }
}

/// Round trip of one layer's weights under per-input-channel `gain`.
pub fn pack(w: &[Vec<f64>], gain: &[f64], group: usize) -> Vec<Vec<f64>> {
    let rows = w.len();
    let cols = w[0].len();
    let ext = span(group, rows);
    let mut out = vec![vec![0.0f64; cols]; rows];
    for i in 0..cols {
        let mut head = 0usize;
        while head < rows {
            let mut top = 0.0f64;
            for o in head..head + ext {
                let v = (w[o][i] * gain[i]).abs();
                if v > top {
                    top = v;
                }
            }
            let step = step_of(top);
            for o in head..head + ext {
                let q = clamp((w[o][i] * gain[i] / step).round());
                out[o][i] = q * step / gain[i];
            }
            head += ext;
        }
    }
    out
}
