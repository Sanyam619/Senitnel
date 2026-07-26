//! One scoring pass over the whole scenario roster.

use std::path::{Path, PathBuf};

use q4_core::load::{Ckpt, Grid, Layout, Panel};
use q4_core::{load, wire};
use q4_knit::admit;

use crate::seat;
use crate::tip;

pub struct Card {
    pub id: String,
    pub perplexity: f64,
    pub top1: f64,
    pub group_size: usize,
    pub tip_epoch: i64,
}

pub struct Desk {
    pub root: PathBuf,
    pub lay: Layout,
    pub row: tip::Row,
    pub grid: Grid,
    pub shards: Vec<String>,
    pub rows: Vec<Vec<f64>>,
}

fn data(root: &Path) -> PathBuf {
    root.join("data")
}

/// Resolve the scored generation and gather the calibration rows behind it.
pub fn open(root: &Path) -> Desk {
    let base = data(root);
    let lay = Layout::read(&base.join("arch/topology.txt"));
    let row = tip::settle(&base);
    let grid = Grid::read(&base.join("quant_grids").join(&row.grid));
    let (shards, rows) = admit::gather(&base, row.epoch, lay.width());
    Desk {
        root: root.to_path_buf(),
        lay,
        row,
        grid,
        shards,
        rows,
    }
}

/// Score every scenario on the roster, in roster order.
pub fn score(desk: &Desk) -> Vec<Card> {
    let base = data(&desk.root);
    let bank = base.join("scales").join(&desk.row.bank);
    let scales = base.join("scales");
    let mut out = Vec::new();
    for (id, slice, start) in load::roster(&base.join("eval/roster.txt")) {
        let ck = Ckpt::read(&base.join("fp16").join(&start), &desk.lay);
        let panel = Panel::read(
            &base.join("eval").join(&slice),
            desk.lay.width(),
            desk.lay.classes,
        );
        let plate = seat::plate(&ck, &desk.lay, &desk.rows, &bank, &scales);
        let pressed = wire::press(&ck, &desk.lay, &plate, desk.grid.group);
        let (perplexity, top1) = wire::tally(&pressed, &desk.lay, &panel.rows, &panel.marks);
        out.push(Card {
            id,
            perplexity,
            top1,
            group_size: desk.grid.group,
            tip_epoch: desk.row.epoch,
        });
    }
    out
}
