//! Phase Z wiring.

use crate::slot_e::{self, Arms};
use std::path::Path;

pub fn load_policy(app: &Path) -> Result<Arms, String> {
    slot_e::arm_q(app)
}

pub fn label_for(name: &str, roster: &[String], peer: Option<&str>, pol: &Arms) -> String {
    match name {
        "alpha" => {
            if roster.iter().any(|l| l == "beacon" || l == "atlas") {
                "provisional_kept".into()
            } else {
                "provisional_dropped".into()
            }
        }
        "beta" => {
            if peer == Some("ridge") {
                "sealed_lease_wins".into()
            } else {
                "newer_lease_wins".into()
            }
        }
        "gamma" => "sealed_lineage".into(),
        "delta" => {
            if pol.fragment_order == "seal_ordinal" {
                "seal_ordinal_weave".into()
            } else {
                "offset_weave".into()
            }
        }
        "epsilon" => {
            if peer == Some("cinder")
                && pol.precedence == "seal_first"
                && pol.borrow_gate == "live_and_clear"
            {
                "clear_sealed_borrow".into()
            } else {
                "policy_mismatch_borrow".into()
            }
        }
        _ => "unknown".into(),
    }
}
