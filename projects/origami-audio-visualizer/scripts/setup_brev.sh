#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${project_dir}"
command -v nvidia-smi >/dev/null || { echo "Run on a GPU-backed Brev instance." >&2; exit 1; }
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -r requirements-ov.txt
echo "Brev setup complete. The GPU run is: bash scripts/run_brev_demo.sh"
