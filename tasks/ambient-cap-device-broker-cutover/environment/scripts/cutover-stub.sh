#!/bin/bash
if [ ! -f /output/broker-cutover.json ]; then
  echo "ledger missing" >&2
  exit 1
fi
echo "ledger present"
