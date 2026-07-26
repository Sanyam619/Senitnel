use std::fs;
use std::path::Path;

/// Counts journal lines for surface status; does not bind hop digests.
pub fn count_lines(path: &Path) -> usize {
    let Ok(text) = fs::read_to_string(path) else {
        return 0;
    };
    text.lines().filter(|l| !l.trim().is_empty()).count()
}
