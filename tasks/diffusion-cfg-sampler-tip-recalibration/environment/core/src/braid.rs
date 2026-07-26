use std::ops::Range;

pub fn braid_k(count: usize, width: usize) -> Vec<Range<usize>> {
    let mut out = Vec::new();
    if width == 0 {
        if count > 0 {
            out.push(0..count);
        }
        return out;
    }
    let mut start = 0usize;
    while start < count {
        let end = (start + width).min(count);
        out.push(start..end);
        start = end;
    }
    out
}
