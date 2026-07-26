#!/usr/bin/env bash
set -uo pipefail

for bin in vlogscan shmbind sqlexport; do
  if [ ! -x "/opt/lab/bin/$bin" ]; then
    echo "missing lab tool: $bin" >&2
    exit 1
  fi
done

rm -f /data/standby/live.db /data/standby/elevation_audit.json

cat > /app/libexec/promote/bind.sh <<'PROMOTE'
#!/usr/bin/env bash
set -euo pipefail

wal=/data/standby/replica.db-wal
shm=/data/standby/replica.db-shm
replica=/data/standby/replica.db
live=/data/standby/live.db
trace=/data/standby/elevation_audit.json

json=$(/opt/lab/bin/vlogscan --file "$wal" --shm "$shm" --json)
cut_ix=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["cut_ix"])' <<<"$json")
mix=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["mix_token"])' <<<"$json")

python3 -c "
import json, pathlib
path = pathlib.Path('$trace')
path.write_text(json.dumps({'version': 1, 'steps': [{'tool': 'vlogscan', 'action': 'inspect'}]}, indent=2))
"

/opt/lab/bin/vlogscan --file "$wal" --truncate-at "$cut_ix"
python3 -c "
import json, pathlib
p = pathlib.Path('$trace')
d = json.loads(p.read_text())
d['steps'].append({'tool': 'vlogscan', 'action': 'trim'})
p.write_text(json.dumps(d, indent=2))
"

/opt/lab/bin/shmbind --shm "$shm" --salt "$mix"
python3 -c "
import json, pathlib
p = pathlib.Path('$trace')
d = json.loads(p.read_text())
d['steps'].append({'tool': 'shmbind', 'action': 'align'})
p.write_text(json.dumps(d, indent=2))
"

/opt/lab/bin/sqlexport --src "$replica" --dst "$live"
python3 -c "
import json, pathlib
p = pathlib.Path('$trace')
d = json.loads(p.read_text())
d['steps'].append({'tool': 'sqlexport', 'action': 'materialize'})
p.write_text(json.dumps(d, indent=2))
"
PROMOTE

chmod +x /app/libexec/promote/bind.sh
install /app/libexec/promote/bind.sh /opt/lab/libexec/promote/bind.sh
/opt/lab/scripts/elevate-standby.sh

if [ ! -f /data/standby/live.db ]; then
  echo "live db not created" >&2
  exit 1
fi

if ! sqlite3 /data/standby/live.db "PRAGMA user_version;" | grep -q '^42$'; then
  echo "user_version mismatch" >&2
  exit 1
fi

row_ct=$(sqlite3 /data/standby/live.db "SELECT COUNT(*) FROM inventory;")
if [ "$row_ct" -lt 5 ]; then
  echo "unexpected row count: $row_ct" >&2
  exit 1
fi

replica_ct=$(sqlite3 -readonly /data/standby/replica.db "SELECT COUNT(*) FROM inventory;" 2>/dev/null || echo 0)
if [ "$replica_ct" -lt 5 ]; then
  echo "replica damaged after elevation" >&2
  exit 1
fi

wal_len=$(stat -c%s /data/standby/replica.db-wal 2>/dev/null || echo 0)
if [ "$wal_len" -gt 0 ]; then
  frame=$((24 + 4096))
  if [ $(((wal_len - 32) % frame)) -ne 0 ]; then
    echo "wal length not frame-aligned: $wal_len" >&2
    exit 1
  fi
fi

echo "elevation complete"
