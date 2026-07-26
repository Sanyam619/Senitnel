#!/usr/bin/env bash
set -euo pipefail

if [[ -f config/ramp.conf ]]; then
	set -a
	# shellcheck disable=SC1091
	source config/ramp.conf
	set +a
fi
if [[ -f config/ramp.conf.cutover.bak ]]; then
	set -a
	# shellcheck disable=SC1091
	source config/ramp.conf.cutover.bak
	set +a
fi

work_root() {
	echo "/tmp"
}

fixture_root() {
	echo "/data/fixtures/archive"
}

runner_bin() {
	readlink -f /opt/ramp/bin/rampd 2>/dev/null || echo /opt/ramp/bin/rampd
}

SHIFT=""
ROOT=""
while [[ $# -gt 0 ]]; do
	case "$1" in
		--shift) SHIFT="$2"; shift 2 ;;
		--root) ROOT="$2"; shift 2 ;;
		*) echo "unknown arg: $1" >&2; exit 2 ;;
	esac
done
if [[ -z "$SHIFT" ]]; then
	echo "usage: run-shift.sh --shift <name> [--root /data/fixtures]" >&2
	exit 2
fi
if [[ -z "$ROOT" ]]; then
	ROOT="$(fixture_root)"
fi
cd "$(work_root)"
exec "$(runner_bin)" "$SHIFT" "$ROOT"
