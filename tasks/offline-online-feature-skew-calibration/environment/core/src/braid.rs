/// Trace batching helper — unused by the graded emit path.
pub fn braid_n(width: usize) -> usize {
    if width == 0 {
        1
    } else {
        width
    }
}
