//! One published scenario: which frozen snapshot it starts from, which channel
//! roster it survives on, which rows it is re-fitted over, and the numbers it
//! reports.

use std::path::Path;

use prune_core::load::{Bank, Ckpt, Panel, Sheet, Topology};
use prune_core::{agreement, span, verdict};
use prune_meld::head;
use prune_meld::{drive, Norms};

use crate::tip::{self, Bound};
use crate::Cell;

fn start_ckpt(root: &Path, topo: &Topology, start: &str) -> Ckpt {
    let file = if start == "resume" {
        "resume.ckpt"
    } else {
        "cold.ckpt"
    };
    Ckpt::read(&root.join("data/dense").join(file), topo)
}

fn held_norms(ck: &Ckpt, keep: &[Vec<usize>]) -> Norms {
    let mut mid = Vec::with_capacity(keep.len());
    let mut spread = Vec::with_capacity(keep.len());
    for (at, rows) in keep.iter().enumerate() {
        mid.push(rows.iter().map(|&i| ck.held_mean[at][i]).collect());
        spread.push(rows.iter().map(|&i| ck.held_var[at][i]).collect());
    }
    Norms { mid, spread }
}

pub fn run(root: &Path, topo: &Topology, bound: &Bound, id: &str, panel: &str, start: &str) -> Cell {
    let panel = Panel::read(
        &root.join("data/eval").join(format!("{panel}.txt")),
        topo.width(),
        topo.classes,
    );
    let ck = start_ckpt(root, topo, start);

    let seated = if start == "resume" && !ck.stamp.is_empty() {
        tip::named(root, &ck.stamp)
    } else {
        Bound {
            tip: bound.tip.clone(),
            epoch: bound.epoch,
            sheet: bound.sheet.clone(),
        }
    };
    let sheet = Sheet::read(&root.join("data/masks").join(&seated.sheet), topo);

    let mut batch: Vec<Vec<f64>> = Vec::new();
    for dom in panel.domains.iter().take(1) {
        let bank = Bank::read(
            &root.join("data/calib").join(format!("shard_{dom}.txt")),
            topo.width(),
        );
        batch.extend(bank.rows);
    }

    let norms = if start == "resume" {
        held_norms(&ck, &sheet.keep)
    } else {
        Norms::fit(&ck, topo, &sheet.keep, &batch)
    };

    let affine = head::refit(
        &ck,
        topo.classes,
        &drive(&ck, topo, &sheet.keep, &norms, &batch),
    );
    let logits = drive(&ck, topo, &sheet.keep, &norms, &panel.rows);
    let extent = span::budget(topo, &sheet.keep);

    Cell {
        id: id.to_string(),
        accuracy: agreement(&verdict(&logits, &affine), &panel.marks),
        dropped: extent.dropped,
        kept: extent.kept,
        epoch: sheet.epoch,
    }
}
