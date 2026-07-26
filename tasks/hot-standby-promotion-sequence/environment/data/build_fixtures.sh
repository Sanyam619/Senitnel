#!/usr/bin/env bash
set -euo pipefail

mkdir -p /data/primary /data/standby /data/fixtures/snapshot

sqlite3 /data/primary/source.db <<'SQL'
PRAGMA user_version=42;
CREATE TABLE inventory(sku TEXT PRIMARY KEY, qty INTEGER NOT NULL);
INSERT INTO inventory(sku, qty) VALUES ('ALPHA', 10), ('BETA', 20), ('GAMMA', 30);
SQL

cp /data/primary/source.db /data/standby/replica.db
cp /data/primary/source.db /data/fixtures/snapshot/source.db

sqlite3 /data/standby/replica.db <<'SQL'
PRAGMA journal_mode=WAL;
PRAGMA wal_autocheckpoint=0;
CREATE TABLE IF NOT EXISTS pad(x BLOB);
BEGIN IMMEDIATE;
INSERT INTO inventory(sku, qty) VALUES ('DELTA', 40);
INSERT INTO inventory(sku, qty) VALUES ('EPSLN', 50);
INSERT INTO pad(x) VALUES(zeroblob(65536));
.shell cp /data/standby/replica.db-wal /data/standby/.wal.capture
.shell cp /data/standby/replica.db-shm /data/standby/.shm.capture
COMMIT;
SQL

if [ ! -f /data/standby/.wal.capture ]; then
  echo "replica wal not created" >&2
  exit 1
fi

mv /data/standby/.wal.capture /data/standby/replica.db-wal
if [ -f /data/standby/.shm.capture ]; then
  mv /data/standby/.shm.capture /data/standby/replica.db-shm
elif [ ! -f /data/standby/replica.db-shm ]; then
  python3 - <<'PY'
from pathlib import Path
Path("/data/standby/replica.db-shm").write_bytes(b"\x00" * 32768)
PY
fi

python3 - <<'PY'
import shutil
from pathlib import Path

wal = Path("/data/standby/replica.db-wal")
shm = Path("/data/standby/replica.db-shm")
primary_wal = Path("/data/primary/source.db-wal")

wal_bytes = wal.read_bytes()
wal.write_bytes(wal_bytes + b"\x00" * 128)

data = bytearray(wal.read_bytes())
if len(data) >= 16:
    data[12:16] = b"\x00\x00\x00\x03"
    wal.write_bytes(data)

shutil.copy(wal, primary_wal)

shm_data = bytearray(shm.read_bytes())
if len(shm_data) >= 8:
    shm_data[4:8] = b"\x00\x00\x00\x00"
    shm.write_bytes(shm_data)
PY

chmod 644 /data/standby/replica.db /data/standby/replica.db-wal || true
chmod 644 /data/standby/replica.db-shm 2>/dev/null || true
chmod 644 /data/primary/source.db /data/primary/source.db-wal || true
chmod 644 /data/fixtures/snapshot/source.db
