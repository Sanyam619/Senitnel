#!/usr/bin/env bash
set -uo pipefail

for bin in chk_a arm_b snap_c; do
  if [ ! -x "/app/bin/$bin" ]; then
    echo "missing lab tool: $bin" >&2
    exit 1
  fi
done

cat > /app/stack-core/src/graph/op_fold.rs <<'RS'
use crate::UnitView;
use std::collections::{BTreeSet, HashMap, VecDeque};

pub fn direct_after(view: &UnitView) -> Vec<String> {
    view.after.clone()
}

fn walk_after(view: &UnitView, all: &HashMap<String, UnitView>, out: &mut BTreeSet<String>) {
    for edge in direct_after(view) {
        if !out.insert(edge.clone()) {
            continue;
        }
        if let Some(dep_view) = all.get(&edge) {
            walk_after(dep_view, all, out);
        }
    }
}

pub fn fold_after(view: &UnitView, all: &HashMap<String, UnitView>) -> BTreeSet<String> {
    let mut out = BTreeSet::new();
    walk_after(view, all, &mut out);
    out
}

pub fn topo(names: &[String], views: &HashMap<String, UnitView>) -> Result<Vec<String>, String> {
    let mut indeg: HashMap<String, usize> = names.iter().map(|n| (n.clone(), 0)).collect();
    let mut edges: HashMap<String, BTreeSet<String>> = HashMap::new();
    for name in names {
        let view = views.get(name).ok_or_else(|| format!("missing {name}"))?;
        let after = fold_after(view, views);
        for dep in after {
            if !names.iter().any(|n| n == &dep) {
                return Err(format!("unknown after dep {dep} for {name}"));
            }
            edges.entry(dep.clone()).or_default().insert(name.clone());
            *indeg.get_mut(name).unwrap() += 1;
        }
    }
    let mut q: VecDeque<String> = indeg
        .iter()
        .filter(|(_, d)| **d == 0)
        .map(|(n, _)| n.clone())
        .collect();
    q.make_contiguous().sort();
    let mut order = Vec::new();
    while let Some(node) = q.pop_front() {
        order.push(node.clone());
        if let Some(nexts) = edges.get(&node) {
            for nxt in nexts {
                let d = indeg.get_mut(nxt).unwrap();
                *d -= 1;
                if *d == 0 {
                    q.push_back(nxt.clone());
                }
            }
        }
    }
    if order.len() != names.len() {
        return Err("cycle detected".into());
    }
    Ok(order)
}
RS

cat > /app/config/aliases.toml <<'TOML'
[map]
TOML

cat > /app/stack-core/src/state/op_activate.rs <<'RS'
use crate::graph::op_fold;
use crate::merge::op_alias;
use crate::unitio;
use crate::{RuntimeRow, UnitView};
use std::collections::HashMap;
use std::fs;
use std::path::Path;

fn ensure_known(name: &str, values: &[String], names: &[String], label: &str) -> Result<(), String> {
    for target in values {
        if !names.iter().any(|n| n == target) {
            return Err(format!("{label} target missing: {target} for {name}"));
        }
    }
    Ok(())
}

pub fn arm(runtime_root: &Path, names: &[String]) -> Result<Vec<String>, String> {
    let mut views = HashMap::new();
    for name in names {
        let merged = runtime_root.join(name).join("merged.ini");
        let mut view = unitio::parse_unit(&merged)?;
        view.after = op_alias::resolve_list(&view.after);
        view.requires = op_alias::resolve_list(&view.requires);
        view.wants = op_alias::resolve_list(&view.wants);
        view.binds_to = op_alias::resolve_list(&view.binds_to);
        views.insert(name.clone(), view);
    }
    op_fold::topo(names, &views)
}

pub fn write_row(runtime_root: &Path, name: &str, order: u32, view: &UnitView) -> Result<(), String> {
    let dir = runtime_root.join(name);
    fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    fs::write(dir.join("state"), "active\n").map_err(|e| e.to_string())?;
    fs::write(dir.join("order"), format!("{order}\n")).map_err(|e| e.to_string())?;
    let hard = view
        .requires
        .iter()
        .chain(view.binds_to.iter())
        .cloned()
        .collect::<Vec<_>>();
    fs::write(dir.join("hard_deps"), format!("{}\n", hard.join("\n"))).map_err(|e| e.to_string())?;
    fs::write(dir.join("soft_deps"), format!("{}\n", view.wants.join("\n"))).map_err(|e| e.to_string())?;
    Ok(())
}

pub fn activate_all(runtime_root: &Path, names: &[String], order: &[String]) -> Result<(), String> {
    let mut views = HashMap::new();
    for name in names {
        let merged = runtime_root.join(name).join("merged.ini");
        let mut view = unitio::parse_unit(&merged)?;
        view.after = op_alias::resolve_list(&view.after);
        view.requires = op_alias::resolve_list(&view.requires);
        view.wants = op_alias::resolve_list(&view.wants);
        view.binds_to = op_alias::resolve_list(&view.binds_to);
        ensure_known(name, &view.requires, names, "require")?;
        ensure_known(name, &view.binds_to, names, "bind")?;
        views.insert(name.clone(), view);
    }
    for (idx, name) in order.iter().enumerate() {
        let view = views.get(name).unwrap();
        write_row(runtime_root, name, (idx + 1) as u32, view)?;
    }
    Ok(())
}
RS

cat > /app/scripts/merge-overrides.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
unit="$1"
src="/data/stack/units/$unit"
drop="/data/stack/overrides/${unit}.d"
out="/data/stack/runtime/$unit"
mkdir -p "$out"
cp "$src" "$out/merged.ini"
if [[ -d "$drop" ]]; then
  mapfile -t files < <(find "$drop" -maxdepth 1 -type f -name '*.conf' | sort -r)
  for frag in "${files[@]}"; do
    while IFS= read -r line || [[ -n "$line" ]]; do
      [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
      key="${line%%=*}"
      val="${line#*=}"
      sed -i "/^${key}=/d" "$out/merged.ini"
      printf '%s=%s\n' "$key" "$val" >> "$out/merged.ini"
    done < "$frag"
  done
fi
SH
chmod 755 /app/scripts/merge-overrides.sh

cat > /app/scripts/stack-up.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
/app/scripts/merge-overrides.sh journal.service
/app/scripts/merge-overrides.sh store.service
/app/scripts/merge-overrides.sh cache.service
/app/scripts/merge-overrides.sh ingress.service
/app/scripts/merge-overrides.sh relay.service
/app/scripts/merge-overrides.sh stack.target
if ! /app/bin/arm_b \
    --units-root /data/stack/units \
    --runtime-root /data/stack/runtime \
    --target stack.target; then
  echo "stackarm activation failed" >&2
  exit 1
fi
SH
chmod 755 /app/scripts/stack-up.sh

if ! (
  cd /app
  cargo build --release --offline
); then
  echo "rebuild failed" >&2
  exit 1
fi

cp /app/target/release/depwalk /app/bin/chk_a
cp /app/target/release/stackarm /app/bin/arm_b
cp /app/target/release/ledgersnap /app/bin/snap_c

rm -rf /data/stack/runtime/*
rm -f /output/rollback-report.json

if ! /app/scripts/stack-up.sh; then
  echo "stack bring-up failed" >&2
  exit 1
fi

if ! /app/bin/chk_a \
    --units-root /data/stack/units \
    --runtime-root /data/stack/runtime; then
  echo "depwalk failed" >&2
  exit 1
fi

if ! /app/bin/snap_c \
    --out /output/rollback-report.json \
    --runtime-root /data/stack/runtime; then
  echo "ledger failed" >&2
  exit 1
fi

python3 - <<'PY'
import json
from pathlib import Path

doc = json.loads(Path("/output/rollback-report.json").read_text())
assert doc.get("version") == 1
names = {row["name"] for row in doc.get("units", [])}
for want in (
    "stack.target",
    "ingress.service",
    "cache.service",
    "store.service",
    "journal.service",
    "relay.service",
):
    assert want in names
for row in doc["units"]:
    assert row["state"] == "active"
    assert row["start_order"] > 0
PY

echo "rollback complete"
