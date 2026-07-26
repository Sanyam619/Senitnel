#!/bin/bash
set -e
if [ -x /app/bin/vfy ]; then
    echo "OK"
else
    echo "FAIL: verifier binary missing"
    exit 1
fi
