//! Readers for the frozen material the desk scores against.

use std::fs;
use std::path::Path;

pub struct Block {
    pub channels: usize,
    pub inputs: usize,
    pub cells: usize,
}

pub struct Topology {
    pub eps: f64,
    pub classes: usize,
    pub blocks: Vec<Block>,
}

pub struct Ckpt {
    pub w: Vec<Vec<Vec<f64>>>,
    pub gain: Vec<Vec<f64>>,
    pub shift: Vec<Vec<f64>>,
    pub held_mean: Vec<Vec<f64>>,
    pub held_var: Vec<Vec<f64>>,
    pub head_w: Vec<Vec<f64>>,
    pub head_b: Vec<f64>,
    pub anchor_mid: Vec<f64>,
    pub anchor_spread: Vec<f64>,
    pub stamp: String,
}

pub struct Sheet {
    pub tip: String,
    pub epoch: i64,
    pub kind: String,
    pub keep: Vec<Vec<usize>>,
}

pub struct Bank {
    pub id: String,
    pub domain: String,
    pub rows: Vec<Vec<f64>>,
}

pub struct Panel {
    pub id: String,
    pub domains: Vec<String>,
    pub rows: Vec<Vec<f64>>,
    pub marks: Vec<usize>,
}

fn slurp(path: &Path) -> String {
    match fs::read_to_string(path) {
        Ok(v) => v,
        Err(e) => panic!("cannot read {}: {e}", path.display()),
    }
}

fn cells(text: &str) -> Vec<Vec<&str>> {
    text.lines()
        .map(|line| line.split_whitespace().collect::<Vec<&str>>())
        .filter(|row| !row.is_empty() && !row[0].starts_with('#'))
        .collect()
}

fn reals(fields: &[&str]) -> Vec<f64> {
    fields
        .iter()
        .map(|f| f.parse::<f64>().unwrap_or_else(|_| panic!("not a number: {f}")))
        .collect()
}

fn whole(field: &str) -> usize {
    field
        .parse::<usize>()
        .unwrap_or_else(|_| panic!("not an index: {field}"))
}

fn fold(flat: Vec<f64>, width: usize) -> Vec<Vec<f64>> {
    assert!(width > 0 && flat.len() % width == 0, "ragged matrix");
    flat.chunks(width).map(|c| c.to_vec()).collect()
}

impl Topology {
    pub fn read(path: &Path) -> Topology {
        let text = slurp(path);
        let mut eps = 1e-5;
        let mut classes = 0usize;
        let mut blocks = Vec::new();
        for row in cells(&text) {
            match row[0] {
                "eps" => eps = reals(&row[1..2])[0],
                "classes" => classes = whole(row[1]),
                "block" => blocks.push(Block {
                    channels: whole(row[2]),
                    inputs: whole(row[3]),
                    cells: whole(row[4]),
                }),
                _ => {}
            }
        }
        assert!(!blocks.is_empty() && classes > 0, "incomplete topology");
        Topology {
            eps,
            classes,
            blocks,
        }
    }

    pub fn width(&self) -> usize {
        self.blocks[0].inputs
    }

    pub fn depth(&self) -> usize {
        self.blocks.len()
    }

    pub fn tail(&self) -> usize {
        self.blocks[self.blocks.len() - 1].channels
    }

    pub fn full(&self) -> Vec<Vec<usize>> {
        self.blocks
            .iter()
            .map(|b| (0..b.channels).collect())
            .collect()
    }
}

impl Ckpt {
    pub fn read(path: &Path, topo: &Topology) -> Ckpt {
        let text = slurp(path);
        let depth = topo.depth();
        let mut ck = Ckpt {
            w: vec![Vec::new(); depth],
            gain: vec![Vec::new(); depth],
            shift: vec![Vec::new(); depth],
            held_mean: vec![Vec::new(); depth],
            held_var: vec![Vec::new(); depth],
            head_w: Vec::new(),
            head_b: Vec::new(),
            anchor_mid: Vec::new(),
            anchor_spread: Vec::new(),
            stamp: String::new(),
        };
        let mut head_flat = Vec::new();
        for row in cells(&text) {
            match row[0] {
                "w" => {
                    let at = whole(row[1]);
                    ck.w[at] = fold(reals(&row[2..]), topo.blocks[at].inputs);
                }
                "gain" => ck.gain[whole(row[1])] = reals(&row[2..]),
                "shift" => ck.shift[whole(row[1])] = reals(&row[2..]),
                "norm_mean" => ck.held_mean[whole(row[1])] = reals(&row[2..]),
                "norm_var" => ck.held_var[whole(row[1])] = reals(&row[2..]),
                "head_w" => head_flat = reals(&row[1..]),
                "head_b" => ck.head_b = reals(&row[1..]),
                "logit_mean" => ck.anchor_mid = reals(&row[1..]),
                "logit_std" => ck.anchor_spread = reals(&row[1..]),
                "mask_stamp" => ck.stamp = row[1].to_string(),
                _ => {}
            }
        }
        ck.head_w = fold(head_flat, topo.tail());
        assert_eq!(ck.head_w.len(), topo.classes, "head rows");
        assert_eq!(ck.head_b.len(), topo.classes, "head bias");
        assert_eq!(ck.anchor_mid.len(), topo.classes, "recorded logit location");
        assert_eq!(ck.anchor_spread.len(), topo.classes, "recorded logit spread");
        for at in 0..depth {
            assert_eq!(ck.w[at].len(), topo.blocks[at].channels, "block {at} rows");
        }
        ck
    }
}

impl Sheet {
    pub fn read(path: &Path, topo: &Topology) -> Sheet {
        let text = slurp(path);
        let mut sheet = Sheet {
            tip: String::new(),
            epoch: -1,
            kind: String::new(),
            keep: vec![Vec::new(); topo.depth()],
        };
        for row in cells(&text) {
            match row[0] {
                "tip" => sheet.tip = row[1].to_string(),
                "epoch" => sheet.epoch = row[1].parse::<i64>().unwrap_or(-1),
                "kind" => sheet.kind = row[1].to_string(),
                "keep" => {
                    let at = whole(row[1]);
                    let mut idx: Vec<usize> = row[2..].iter().map(|f| whole(f)).collect();
                    idx.sort_unstable();
                    sheet.keep[at] = idx;
                }
                _ => {}
            }
        }
        for (at, blk) in topo.blocks.iter().enumerate() {
            assert!(!sheet.keep[at].is_empty(), "empty channel roster at {at}");
            assert!(
                sheet.keep[at].iter().all(|&i| i < blk.channels),
                "channel out of range at {at}"
            );
        }
        sheet
    }

    pub fn kept(&self) -> usize {
        self.keep.iter().map(|k| k.len()).sum()
    }
}

impl Bank {
    pub fn read(path: &Path, width: usize) -> Bank {
        let text = slurp(path);
        let mut bank = Bank {
            id: String::new(),
            domain: String::new(),
            rows: Vec::new(),
        };
        for row in cells(&text) {
            match row[0] {
                "id" => bank.id = row[1].to_string(),
                "domain" => bank.domain = row[1].to_string(),
                "row" => {
                    let vals = reals(&row[1..]);
                    assert_eq!(vals.len(), width, "calibration row width");
                    bank.rows.push(vals);
                }
                _ => {}
            }
        }
        assert!(!bank.rows.is_empty(), "empty calibration bank");
        bank
    }
}

impl Panel {
    pub fn read(path: &Path, width: usize, classes: usize) -> Panel {
        let text = slurp(path);
        let mut panel = Panel {
            id: String::new(),
            domains: Vec::new(),
            rows: Vec::new(),
            marks: Vec::new(),
        };
        for row in cells(&text) {
            match row[0] {
                "id" => panel.id = row[1].to_string(),
                "domain" => panel.domains = row[1..].iter().map(|d| d.to_string()).collect(),
                "row" => {
                    let vals = reals(&row[1..]);
                    assert_eq!(vals.len(), width + 1, "evaluation row width");
                    let mark = vals[width] as usize;
                    assert!(mark < classes, "label out of range");
                    panel.rows.push(vals[..width].to_vec());
                    panel.marks.push(mark);
                }
                _ => {}
            }
        }
        assert!(!panel.rows.is_empty(), "empty evaluation panel");
        panel
    }
}
