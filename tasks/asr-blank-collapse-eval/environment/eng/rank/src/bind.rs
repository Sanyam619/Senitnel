use std::path::Path;

use crate::epoch;
use crate::fuse;

pub struct Seat {
    pub at: u32,
    pub name: String,
    pub sheet: String,
    pub route: String,
    pub weight: f64,
}

pub fn seat(root: &Path) -> Seat {
    let rows = epoch::rows(root);
    let out = epoch::out_set(root);
    let at = epoch::pick_e(&rows, &out);
    let row = rows
        .iter()
        .find(|r| r.at == at)
        .unwrap_or_else(|| panic!("no registry row at {at}"));
    let weight = fuse::row_w(&row.sheet, at, root);
    Seat {
        at,
        name: row.name.clone(),
        sheet: row.sheet.clone(),
        route: row.route.clone(),
        weight,
    }
}
