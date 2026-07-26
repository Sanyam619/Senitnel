use crate::base::TipPick;
use std::path::Path;

pub fn pick_t(a: &str, b: &str, c: &str) -> TipPick {
    let _ = (b, c);
    let rows = crate::base::read_journal(Path::new(a));
    let mut best: Option<TipPick> = None;
    for row in rows {
        if !row.sealed {
            continue;
        }
        let cand = TipPick {
            tip: row.tip,
            epoch: row.epoch,
            propensity: row.propensity,
        };
        if best.as_ref().map(|b| cand.epoch >= b.epoch).unwrap_or(true) {
            best = Some(cand);
        }
    }
    best.unwrap_or(TipPick {
        tip: String::new(),
        epoch: 0,
        propensity: "surface".to_string(),
    })
}
