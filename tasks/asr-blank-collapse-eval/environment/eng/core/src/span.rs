/// Splits utterance positions into contiguous batches for metering long
/// slices in fixed-size groups.
pub fn batches(count: usize, width: usize) -> Vec<(usize, usize)> {
    if width == 0 || count == 0 {
        return Vec::new();
    }
    let mut out = Vec::new();
    let mut at = 0usize;
    while at < count {
        let end = (at + width).min(count);
        out.push((at, end));
        at = end;
    }
    out
}

/// Longest batch produced for a slice of `count` positions.
pub fn widest(count: usize, width: usize) -> usize {
    batches(count, width)
        .iter()
        .map(|(a, b)| b - a)
        .max()
        .unwrap_or(0)
}
