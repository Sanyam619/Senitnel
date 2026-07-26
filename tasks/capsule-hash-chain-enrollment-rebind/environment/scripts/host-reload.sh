#!/bin/bash
# Simulate a host reload that promotes the on-disk bundle into the live slot.
# The runtime state file is left as-is.
set -e
cp /app/data/roots/disk.bundle /app/data/roots/live.bundle
