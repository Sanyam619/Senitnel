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
        };
        if best.as_ref().map(|x| cand.epoch >= x.epoch).unwrap_or(true) {
            best = Some(cand);
        }
    }
    best.unwrap_or(TipPick {
        tip: String::new(),
        epoch: 0,
    })
}
