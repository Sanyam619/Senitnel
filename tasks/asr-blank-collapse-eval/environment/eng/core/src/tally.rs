/// Levenshtein distance between two sequences.
pub fn drift<T: PartialEq>(a: &[T], b: &[T]) -> usize {
    let mut prev: Vec<usize> = (0..=b.len()).collect();
    let mut cur: Vec<usize> = vec![0; b.len() + 1];
    for i in 1..=a.len() {
        cur[0] = i;
        for j in 1..=b.len() {
            let sub = prev[j - 1] + if a[i - 1] == b[j - 1] { 0 } else { 1 };
            let del = prev[j] + 1;
            let ins = cur[j - 1] + 1;
            cur[j] = sub.min(del).min(ins);
        }
        std::mem::swap(&mut prev, &mut cur);
    }
    prev[b.len()]
}

/// Accumulates unit-level and character-level drift over a slice.
#[derive(Default)]
pub struct Meter {
    unit_drift: usize,
    unit_span: usize,
    char_drift: usize,
    char_span: usize,
}

impl Meter {
    pub fn new() -> Meter {
        Meter::default()
    }

    pub fn add(&mut self, hyp: &[String], reference: &[String]) {
        self.unit_drift += drift(hyp, reference);
        self.unit_span += reference.len();
        let hchars: Vec<char> = hyp.join(" ").chars().collect();
        let rchars: Vec<char> = reference.join(" ").chars().collect();
        self.char_drift += drift(&hchars, &rchars);
        self.char_span += rchars.len();
    }

    pub fn unit_rate(&self) -> f64 {
        self.unit_drift as f64 / self.unit_span as f64
    }

    pub fn char_rate(&self) -> f64 {
        self.char_drift as f64 / self.char_span as f64
    }
}
