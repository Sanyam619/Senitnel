#!/bin/bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/cargo/bin:/app/bin:${PATH}"

test -d /app/config/l7
test -x /app/bin/indexctl
mkdir -p /output /app/ops/staging

read -r HEAD < <(
python3 <<'PY'
import json
from pathlib import Path

head = 0
for path in sorted(Path("/app/data/index/snapshots").glob("tier_*.jsonl")):
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        head = max(head, int(json.loads(line)["gen"]))
if head == 0:
    raise SystemExit("could not derive snapshot head")
print(head)
PY
)

python3 <<PY
import json

head = int("${HEAD}")
# Preflight fixture expectations under normative policy (half-open, revokes, high floor).
assert head == 4
PY

sed -i 's/^bound_mode = .*/bound_mode = "half_open"/' /app/config/l7/k9.toml
sed -i 's/^honor_revokes = .*/honor_revokes = true/' /app/config/l7/k9.toml
sed -i 's/^adv_live_only = .*/adv_live_only = true/' /app/config/l7/k9.toml
sed -i 's/^adv_floor = .*/adv_floor = "high"/' /app/config/l7/k9.toml
sed -i 's/^audit_stamp = .*/audit_stamp = "applied"/' /app/config/l7/k9.toml

cat > /app/rsx/core/src/q_slot.rs <<'RSFIX'
use serde::Deserialize;
use std::collections::HashMap;
use std::fs;
use std::path::Path;

#[derive(Debug, Deserialize, Clone)]
pub struct YankWindow {
    #[serde(rename = "crate")]
    pub crate_name: String,
    pub vers: String,
    pub from: u64,
    pub until: Option<u64>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct RevokeRow {
    #[serde(rename = "crate")]
    pub crate_name: String,
    pub vers: String,
    pub at: u64,
}

pub fn read_bound_half_open() -> bool {
    let text = fs::read_to_string("/app/config/l7/k9.toml").unwrap_or_default();
    for line in text.lines() {
        let trimmed = line.trim();
        if !trimmed.starts_with("bound_mode") {
            continue;
        }
        let val = trimmed.split('=').nth(1).unwrap_or("").trim().trim_matches('"');
        return val == "half_open";
    }
    false
}

pub fn read_honor_revokes() -> bool {
    let text = fs::read_to_string("/app/config/l7/k9.toml").unwrap_or_default();
    for line in text.lines() {
        let trimmed = line.trim();
        if !trimmed.starts_with("honor_revokes") {
            continue;
        }
        let val = trimmed.split('=').nth(1).unwrap_or("false").trim();
        return val == "true";
    }
    false
}

pub fn load_windows(data_root: &Path) -> Result<Vec<YankWindow>, String> {
    let raw = fs::read_to_string(data_root.join("yanks/windows.jsonl")).map_err(|e| e.to_string())?;
    let mut out = Vec::new();
    for line in raw.lines() {
        if line.trim().is_empty() {
            continue;
        }
        out.push(serde_json::from_str(line).map_err(|e| e.to_string())?);
    }
    Ok(out)
}

pub fn load_revokes(data_root: &Path) -> Result<HashMap<(String, String), u64>, String> {
    let path = data_root.join("yanks/revokes.jsonl");
    let mut out = HashMap::new();
    if !path.exists() {
        return Ok(out);
    }
    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    for line in raw.lines() {
        if line.trim().is_empty() {
            continue;
        }
        let row: RevokeRow = serde_json::from_str(line).map_err(|e| e.to_string())?;
        out.insert((row.crate_name, row.vers), row.at);
    }
    Ok(out)
}

pub fn yank_holds(
    window: &YankWindow,
    gen: u64,
    half_open: bool,
    revokes: &HashMap<(String, String), u64>,
    honor_revokes: bool,
) -> bool {
    if window.from > gen {
        return false;
    }
    if honor_revokes {
        if let Some(at) = revokes.get(&(window.crate_name.clone(), window.vers.clone())) {
            if *at <= gen {
                return false;
            }
        }
    }
    match window.until {
        None => true,
        Some(until) => {
            if half_open {
                gen < until
            } else {
                gen <= until
            }
        }
    }
}

pub fn active_yank_set(
    data_root: &Path,
    gen: u64,
) -> Result<std::collections::BTreeSet<(String, String)>, String> {
    let half_open = read_bound_half_open();
    let honor = read_honor_revokes();
    let windows = load_windows(data_root)?;
    let revokes = load_revokes(data_root)?;
    let mut yanked = std::collections::BTreeSet::new();
    for w in &windows {
        if yank_holds(w, gen, half_open, &revokes, honor) {
            yanked.insert((w.crate_name.clone(), w.vers.clone()));
        }
    }
    Ok(yanked)
}
RSFIX

cat > /app/rsx/core/src/k_net.rs <<'RSFIX'
use crate::DepRow;
use crate::VersionRow;
use std::collections::HashMap;

fn is_optional(dep: &DepRow) -> bool {
    dep.kind.as_deref() == Some("optional")
}

pub fn installable_rows(
    entries: &[VersionRow],
    yanked: &std::collections::BTreeSet<(String, String)>,
) -> Vec<(String, String)> {
    let index: HashMap<(String, String), &VersionRow> = entries
        .iter()
        .map(|r| ((r.name.clone(), r.vers.clone()), r))
        .collect();
    let mut memo: HashMap<(String, String), bool> = HashMap::new();

    fn ok(
        key: &(String, String),
        index: &HashMap<(String, String), &VersionRow>,
        yanked: &std::collections::BTreeSet<(String, String)>,
        memo: &mut HashMap<(String, String), bool>,
    ) -> bool {
        if let Some(cached) = memo.get(key) {
            return *cached;
        }
        if yanked.contains(key) {
            memo.insert(key.clone(), false);
            return false;
        }
        let Some(body) = index.get(key) else {
            memo.insert(key.clone(), false);
            return false;
        };
        for dep in &body.deps {
            if is_optional(dep) {
                continue;
            }
            let dkey = (dep.crate_name.clone(), dep.version.clone());
            if !ok(&dkey, index, yanked, memo) {
                memo.insert(key.clone(), false);
                return false;
            }
        }
        memo.insert(key.clone(), true);
        true
    }

    let mut out = Vec::new();
    for row in entries {
        let key = (row.name.clone(), row.vers.clone());
        if ok(&key, &index, yanked, &mut memo) {
            out.push(key);
        }
    }
    out
}
RSFIX

python3 <<'PY'
from pathlib import Path

path = Path("/app/rsx/core/src/lib.rs")
text = path.read_text()
old = """    let floor_rank = sev_rank(&floor);
    let _ = floor_rank;
    let mut advisories = Vec::new();
    for adv in load_advisories(data_root)? {
        let crate_name = adv.get("crate").and_then(|v| v.as_str()).unwrap_or("").to_string();
        let vers = adv.get("vers").and_then(|v| v.as_str()).unwrap_or("").to_string();
        let from = adv.get("from").and_then(|v| v.as_u64()).unwrap_or(0);
        let sev = adv.get("severity").and_then(|v| v.as_str()).unwrap_or("low");
        if from > gen {
            continue;
        }
        if live_only && !yanked_set.contains(&(crate_name.clone(), vers.clone())) {
            continue;
        }
        let _ = sev;
        advisories.push(adv);
    }"""
new = """    let floor_rank = sev_rank(&floor);
    let mut advisories = Vec::new();
    for adv in load_advisories(data_root)? {
        let crate_name = adv.get("crate").and_then(|v| v.as_str()).unwrap_or("").to_string();
        let vers = adv.get("vers").and_then(|v| v.as_str()).unwrap_or("").to_string();
        let from = adv.get("from").and_then(|v| v.as_u64()).unwrap_or(0);
        let sev = adv.get("severity").and_then(|v| v.as_str()).unwrap_or("low");
        if from > gen {
            continue;
        }
        if live_only && !yanked_set.contains(&(crate_name.clone(), vers.clone())) {
            continue;
        }
        if sev_rank(sev) < floor_rank {
            continue;
        }
        advisories.push(adv);
    }"""
if old not in text:
    raise SystemExit("rust advisory filter block missing")
path.write_text(text.replace(old, new, 1))
PY

python3 <<'PY'
from pathlib import Path

path = Path("/app/scan/internal/m4/live.go")
text = path.read_text()
old = """\tactive := map[string]bool{}
\t_ = halfOpen
\t_ = honor
\t_ = floor
\tfor _, w := range win {
\t\tif yankActive(w, gen, false, revokes, false) {
\t\t\tactive[w.Crate+"@"+w.Vers] = true
\t\t}
\t}"""
new = """\tactive := map[string]bool{}
\tfor _, w := range win {
\t\tif yankActive(w, gen, halfOpen, revokes, honor) {
\t\t\tactive[w.Crate+"@"+w.Vers] = true
\t\t}
\t}"""
if old not in text:
    raise SystemExit("go active-yank loop missing")
text = text.replace(old, new, 1)
old2 = """\t\tif liveOnly && !active[row.Crate+"@"+row.Vers] {
\t\t\tcontinue
\t\t}
\t\trows = append(rows, row)"""
new2 = """\t\tif liveOnly && !active[row.Crate+"@"+row.Vers] {
\t\t\tcontinue
\t\t}
\t\tif sevRank(row.Severity) < floor {
\t\t\tcontinue
\t\t}
\t\trows = append(rows, row)"""
if old2 not in text:
    raise SystemExit("go severity filter block missing")
path.write_text(text.replace(old2, new2, 1))
PY

(cd /app/scan && CGO_ENABLED=0 go build -o /app/bin/advscan ./cmd/advscan)
(cd /app/rsx && cargo build --release --locked --offline -p indexctl)
install -m 755 /app/rsx/target/release/indexctl /app/bin/indexctl

/app/bin/indexctl report --out /output/yank-reconcile.json

report_gen=$(python3 -c "import json; print(json.load(open('/output/yank-reconcile.json'))['snapshot_gen'])")
test "${report_gen}" -eq "${HEAD}"
test "$(/app/bin/advscan window)" -eq "${HEAD}"

python3 <<'PY'
import json
from pathlib import Path

report = json.loads(Path("/output/yank-reconcile.json").read_text())
yanked = {(r["crate"], r["version"]) for r in report["yanked"]}
installable = {(r["crate"], r["version"]) for r in report["installable"]}
assert yanked == {("beta-util", "1.2.0"), ("sigma-kit", "0.1.0")}
assert ("gamma-api", "0.9.1") not in yanked
assert ("theta-lib", "0.2.0") not in yanked
assert ("theta-lib", "0.2.0") in installable
assert ("epsilon-net", "1.0.0") not in installable
assert ("omega-lib", "1.0.0") in installable
assert ("zeta-tool", "1.0.0") in installable
assert ("alpha-core", "1.1.0") not in installable
assert ("delta-cli", "2.1.0") not in installable
assert report["snapshot_gen"] == 4
PY

fresh=/tmp/oracle-fresh-report.json
/app/bin/indexctl report --out "${fresh}"
python3 -c "import json,sys; a=json.load(open('/output/yank-reconcile.json')); b=json.load(open(sys.argv[1])); assert a==b" "${fresh}"
test "$(/app/bin/advscan digest)" = "$(python3 -c "import json; print(json.load(open('/output/yank-reconcile.json'))['advisory_digest'])")"

echo "complete" > /app/ops/staging/workflow.complete
