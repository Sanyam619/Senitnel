#!/usr/bin/env bash
set -euo pipefail
cd /opt/ramp

cat > config/ramp.conf <<'EOF'
# ramp batch runtime fragment (winter cutover)
FIXTURE_ROOT=/data/fixtures
WORK_DIR=/opt/ramp
RUNNER_LINK=/opt/ramp/bin/rampd
RUNNER_ACTIVE=/opt/ramp/bin/rampd.active
RAMP_OUT_ROOT=/data/out
EOF

rm -f config/ramp.conf.cutover.bak

cp -f bin/rampd.active bin/rampd

cat > scripts/run-shift.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

if [[ -f config/ramp.conf ]]; then
  set -a
  # shellcheck disable=SC1091
  source config/ramp.conf
  set +a
fi

work_root() {
  echo "${WORK_DIR:-/opt/ramp}"
}

fixture_root() {
  echo "${FIXTURE_ROOT:-/data/fixtures}"
}

runner_bin() {
  echo "${RUNNER_ACTIVE:-/opt/ramp/bin/rampd.active}"
}

shift_name=""
root_dir=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --shift) shift_name="$2"; shift 2 ;;
    --root) root_dir="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
if [[ -z "$shift_name" ]]; then
  echo "usage: run-shift.sh --shift <name> [--root /data/fixtures]" >&2
  exit 2
fi
if [[ -z "$root_dir" ]]; then
  root_dir="$(fixture_root)"
fi
cd "$(work_root)"
exec "$(runner_bin)" "$shift_name" "$root_dir"
EOF
chmod 0755 scripts/run-shift.sh

for shift in shift_w1206 shift_w1207 shift_w1208 shift_w1209 shift_w1210 shift_w1211 shift_w1212; do
  /opt/ramp/scripts/run-shift.sh --shift "$shift" --root /data/fixtures
done
