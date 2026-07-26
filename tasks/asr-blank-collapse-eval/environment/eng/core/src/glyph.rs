use std::collections::HashMap;
use std::fs;
use std::path::Path;

pub struct Lex {
    pub units: Vec<String>,
    index: HashMap<String, usize>,
}

impl Lex {
    pub fn load(path: &Path) -> Lex {
        let text = fs::read_to_string(path).unwrap_or_else(|e| panic!("{}: {e}", path.display()));
        let mut units = Vec::new();
        let mut index = HashMap::new();
        for line in text.lines() {
            let line = line.trim();
            if line.is_empty() {
                continue;
            }
            let mut parts = line.split_whitespace();
            let at: usize = parts.next().unwrap().parse().unwrap();
            let unit = parts.next().unwrap().to_string();
            if units.len() <= at {
                units.resize(at + 1, String::new());
            }
            index.insert(unit.clone(), at);
            units[at] = unit;
        }
        Lex { units, index }
    }

    pub fn width(&self) -> usize {
        self.units.len()
    }

    pub fn text(&self, seq: &[usize]) -> Vec<String> {
        seq.iter().map(|i| self.units[*i].clone()).collect()
    }
}

/// One reference line: the utterance stem and its unit indices.
pub struct Line {
    pub stem: String,
    pub units: Vec<usize>,
}

pub fn lines(path: &Path, lex: &Lex) -> Vec<Line> {
    let text = fs::read_to_string(path).unwrap_or_else(|e| panic!("{}: {e}", path.display()));
    let mut out = Vec::new();
    for line in text.lines() {
        let line = line.trim_end();
        if line.is_empty() {
            continue;
        }
        let (stem, rest) = line.split_once('\t').expect("reference line shape");
        let units = rest
            .split_whitespace()
            .map(|w| *lex.index.get(w).unwrap_or_else(|| panic!("unit {w}")))
            .collect();
        out.push(Line {
            stem: stem.to_string(),
            units,
        });
    }
    out
}
