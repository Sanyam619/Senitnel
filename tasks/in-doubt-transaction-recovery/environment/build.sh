#!/bin/bash
set -euo pipefail
rm -rf /app/build/classes
mkdir -p /app/build/classes
javac -d /app/build/classes $(find /app/src/main/java -name '*.java' | sort)
