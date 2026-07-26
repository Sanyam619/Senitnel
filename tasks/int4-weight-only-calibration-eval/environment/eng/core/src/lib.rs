//! Shared material readers, dense evaluation and the four-bit round trip.

pub mod fold;
pub mod load;
pub mod wire;

/// Where the desk keeps its frozen material.
pub fn root() -> std::path::PathBuf {
    std::path::PathBuf::from(std::env::var("Q4_ROOT").unwrap_or_else(|_| "/app".to_string()))
}
