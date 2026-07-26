//! Readers for the frozen material the desk scores against.

use std::fs;
use std::path::Path;

pub struct Layout {
    pub eps: f64,
    pub classes: usize,
    pub inn: Vec<usize>,
    pub out: Vec<usize>,
}

pub struct Ckpt {
    pub w: Vec<Vec<Vec<f64>>>,
    pub b: Vec<Vec<f64>>,
    pub source: String,
    pub stamp: String,
    pub sheet_ref: String,
}

pub struct Bank {
    pub id: String,
    pub revision: String,
    pub gain: Vec<Vec<f64>>,
}

pub struct Shard {
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

pub struct Grid {
    pub tip: String,
    pub epoch: i64,
    pub kind: String,
    pub group: usize,
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
        .unwrap_or_else(|_| panic!("not a count: {field}"))
}

fn split(flat: Vec<f64>, width: usize) -> Vec<Vec<f64>> {
    assert!(width > 0 && flat.len() % width == 0, "ragged matrix");
    flat.chunks(width).map(|c| c.to_vec()).collect()
}

impl Layout {
    pub fn read(path: &Path) -> Layout {
        let text = slurp(path);
        let mut eps = 1e-6;
        let mut classes = 0usize;
        let mut slots: Vec<(usize, usize, usize)> = Vec::new();
        for row in cells(&text) {
            match row[0] {
                "eps" => eps = reals(&row[1..2])[0],
                "classes" => classes = whole(row[1]),
                "layer" => slots.push((whole(row[1]), whole(row[2]), whole(row[3]))),
                _ => {}
            }
        }
        assert!(!slots.is_empty() && classes > 0, "incomplete layout");
        slots.sort_by_key(|s| s.0);
        Layout {
            eps,
            classes,
            inn: slots.iter().map(|s| s.2).collect(),
            out: slots.iter().map(|s| s.1).collect(),
        }
    }

    pub fn depth(&self) -> usize {
        self.inn.len()
    }

    pub fn width(&self) -> usize {
        self.inn[0]
    }
}

impl Ckpt {
    pub fn read(path: &Path, lay: &Layout) -> Ckpt {
        let text = slurp(path);
        let depth = lay.depth();
        let mut ck = Ckpt {
            w: vec![Vec::new(); depth],
            b: vec![Vec::new(); depth],
            source: String::new(),
            stamp: String::new(),
            sheet_ref: String::new(),
        };
        for row in cells(&text) {
            match row[0] {
                "w" => {
                    let at = whole(row[1]);
                    ck.w[at] = split(reals(&row[2..]), lay.inn[at]);
                }
                "b" => ck.b[whole(row[1])] = reals(&row[2..]),
                "source" => ck.source = row[1].to_string(),
                "grid_stamp" => ck.stamp = row[1].to_string(),
                "scale_ref" => ck.sheet_ref = row[1].to_string(),
                _ => {}
            }
        }
        for at in 0..depth {
            assert_eq!(ck.w[at].len(), lay.out[at], "layer {at} rows");
            assert_eq!(ck.b[at].len(), lay.out[at], "layer {at} offsets");
        }
        assert_eq!(ck.w[depth - 1].len(), lay.classes, "class count");
        ck
    }
}

impl Bank {
    pub fn read(path: &Path, lay: &Layout) -> Bank {
        let text = slurp(path);
        let mut bank = Bank {
            id: String::new(),
            revision: String::new(),
            gain: vec![Vec::new(); lay.depth()],
        };
        for row in cells(&text) {
            match row[0] {
                "id" => bank.id = row[1].to_string(),
                "revision" => bank.revision = row[1].to_string(),
                "gain" => bank.gain[whole(row[1])] = reals(&row[2..]),
                _ => {}
            }
        }
        for at in 0..lay.depth() {
            assert_eq!(bank.gain[at].len(), lay.inn[at], "bank width at {at}");
        }
        bank
    }
}

impl Shard {
    pub fn read(path: &Path, width: usize) -> Shard {
        let text = slurp(path);
        let mut shard = Shard {
            id: String::new(),
            domain: String::new(),
            rows: Vec::new(),
        };
        for row in cells(&text) {
            match row[0] {
                "id" => shard.id = row[1].to_string(),
                "domain" => shard.domain = row[1].to_string(),
                "row" => {
                    let vals = reals(&row[1..]);
                    assert_eq!(vals.len(), width, "calibration row width");
                    shard.rows.push(vals);
                }
                _ => {}
            }
        }
        assert!(!shard.rows.is_empty(), "empty calibration shard");
        shard
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
        assert!(!panel.rows.is_empty(), "empty evaluation slice");
        panel
    }
}

impl Grid {
    pub fn read(path: &Path) -> Grid {
        let text = slurp(path);
        let mut grid = Grid {
            tip: String::new(),
            epoch: -1,
            kind: String::new(),
            group: 0,
        };
        for row in cells(&text) {
            match row[0] {
                "tip" => grid.tip = row[1].to_string(),
                "epoch" => grid.epoch = row[1].parse::<i64>().unwrap_or(-1),
                "kind" => grid.kind = row[1].to_string(),
                "group" => grid.group = whole(row[1]),
                _ => {}
            }
        }
        assert!(!grid.tip.is_empty(), "grouping sheet has no name");
        grid
    }
}

/// One line of the scenario roster: id, slice, starting snapshot.
pub fn roster(path: &Path) -> Vec<(String, String, String)> {
    let text = slurp(path);
    let mut out = Vec::new();
    for row in cells(&text) {
        if row[0] == "scenario" && row.len() >= 4 {
            out.push((row[1].to_string(), row[2].to_string(), row[3].to_string()));
        }
    }
    assert!(!out.is_empty(), "empty scenario roster");
    out
}
