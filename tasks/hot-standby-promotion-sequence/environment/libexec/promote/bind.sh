#!/usr/bin/env bash
set -euo pipefail

WAL=/data/standby/replica.db-wal
SHM=/data/standby/replica.db-shm
TARGET_LEN=$(stat -c%s /data/primary/source.db-wal)

/opt/lab/bin/logpack --file "$WAL" --target-len "$TARGET_LEN"
/opt/lab/bin/sqlexport --src /data/standby/replica.db --dst /data/standby/live.db
