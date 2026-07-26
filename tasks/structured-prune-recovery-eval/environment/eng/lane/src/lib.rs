//! The evaluation desk: the roster of published scenarios and the numbers each
//! one reports.

pub mod seat;
pub mod tip;

use std::fs;
use std::path::{Path, PathBuf};

use prune_core::load::Topology;

pub struct Cell {
    pub id: String,
    pub accuracy: f64,
    pub dropped: f64,
    pub kept: f64,
    pub epoch: i64,
}

struct Slot {
    id: String,
    panel: String,
    start: String,
}

pub struct Desk {
    root: PathBuf,
    topo: Topology,
    slots: Vec<Slot>,
}

impl Desk {
    pub fn open(root: &Path) -> Desk {
        let topo = Topology::read(&root.join("data/arch/topology.txt"));
        let text = fs::read_to_string(root.join("data/eval/roster.txt"))
            .unwrap_or_else(|e| panic!("cannot read the published roster: {e}"));
        let mut slots = Vec::new();
        for line in text.lines() {
            let row: Vec<&str> = line.split_whitespace().collect();
            if row.len() < 4 || row[0] != "scenario" {
                continue;
            }
            slots.push(Slot {
                id: row[1].to_string(),
                panel: row[2].to_string(),
                start: row[3].to_string(),
            });
        }
        assert!(!slots.is_empty(), "the published roster is empty");
        Desk {
            root: root.to_path_buf(),
            topo,
            slots,
        }
    }

    pub fn cells(&self) -> Vec<Cell> {
        let bound = tip::settled(&self.root);
        self.slots
            .iter()
            .map(|slot| {
                seat::run(
                    &self.root,
                    &self.topo,
                    &bound,
                    &slot.id,
                    &slot.panel,
                    &slot.start,
                )
            })
            .collect()
    }
}
