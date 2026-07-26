#!/usr/bin/env bash
set -euo pipefail
sqlite3 -readonly /data/standby/replica.db "SELECT sku, qty FROM inventory ORDER BY sku;"
