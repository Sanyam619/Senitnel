#!/usr/bin/env bash
set -euo pipefail
/opt/rly/bin/sealmake --lane floor --out /output/attestation-bundle.json
/opt/rly/bin/floorcheck --bundle /output/attestation-bundle.json --verdict /output/gate-verdict.json
