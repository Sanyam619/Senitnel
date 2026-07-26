//! Phase Y wiring.

use std::path::Path;

use crate::emit_d;
use crate::skim_c;
use crate::slot_e::Arms;

pub fn payload_for(ep: &str) -> Result<Vec<u8>, String> {
    skim_c::draw_k(ep)
}

pub fn frag_for(dir: &Path, pol: &Arms) -> Result<Vec<u8>, String> {
    emit_d::fold_z(dir, pol)
}
