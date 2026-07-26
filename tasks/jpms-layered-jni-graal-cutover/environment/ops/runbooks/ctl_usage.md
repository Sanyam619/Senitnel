# packctl packaging probe
#
# Builds modular units under /app/unit, applies the active packaging lattice,
# links the JNI shared library under /app/native, then writes
# /output/pack-report.json for every launch mode listed in /app/ops/matrix.toml.
#
# Invoke from /app:
#   /app/bin/packctl
#
# The installed entrypoint is /app/bin/packctl. Prefer that path in scripts and
# probes. Cutover notes live under /app/link/; active profile selection is under
# /app/data/state/ and /app/config/profiles/.
#
# When a mode stays degraded, inspect the probe fragments under /app/build/ and
# the reachability metadata packctl materializes — do not invent a report by hand.
