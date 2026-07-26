#!/bin/sh
set -eu
ROOT=/data/token
touch "$ROOT/reload.marker"

tr -d '\r' < "$ROOT/inventory.txt" > /tmp/inv.txt
tr -d '\r' < "$ROOT/sessions.txt" > /tmp/sess.txt

awk '
  FNR==NR {
    if ($0 ~ /^#/ || NF < 2) next
    roles[$1] = $2
    next
  }
  BEGIN { print "# slot pin_alive ttl" }
  /^#/ || NF < 3 { next }
  {
    slot = $1
    role = roles[slot]
    if (role == "archive") {
      print slot, 1, 86400
    } else {
      print slot, 0, 86400
    }
  }
' /tmp/inv.txt /tmp/sess.txt > /tmp/sess.next

mv /tmp/sess.next "$ROOT/sessions.txt"
echo "reload-harness: marked"
