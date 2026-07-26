#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/n4"
make clean all
mkdir -p "$ROOT/bin"
cd "$ROOT"
cargo build --release --locked -p q7
cp -f "$ROOT/target/release/runtime" "$ROOT/bin/runtime"
cc -O2 -o "$ROOT/bin/surfprobe" "$ROOT/surf/surfprobe.c" -L"$ROOT/n4" -lkern -Wl,-rpath,"$ROOT/n4"
chmod +x "$ROOT/eval/run_eval.sh" "$ROOT/eval/run_surface.sh"
echo "build_ok"
