use crate::base::{self, FeatMap};
use std::path::Path;

pub fn pull_m(root: &Path, tip: &str) -> FeatMap {
    let path = root.join("online").join(format!("{tip}.json"));
    base::read_tip_means(&path)
}

pub fn pull_shadow(root: &Path) -> FeatMap {
    base::read_tip_means(&root.join("online").join("tip_live.json"))
}

pub fn blend(on: &FeatMap, shadow: &FeatMap, sel: &str) -> FeatMap {
    crate::mesh::mesh_k(on, shadow, sel)
}
