#!/usr/bin/env bash
set -e
export PYTHONPATH="$(dirname "$0")/.."
cd "$(dirname "$0")/.."
python scripts/seed_admin.py
