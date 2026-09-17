#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${project_dir}"
test -x .venv/bin/python || { echo "Run scripts/setup_brev.sh first." >&2; exit 1; }
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m origami_visualizer.usd_asset --width 20 --height 20 --output assets/origami_20x20.usda
.venv/bin/python run_demo.py --width 20 --height 20 --seconds 6
if .venv/bin/python -c "import ovphysx, ovrtx, ovstage" 2>/dev/null; then
  .venv/bin/python server/ovphysx_bridge.py --scene assets/origami_20x20.usda --seconds 30
  .venv/bin/python server/ovrtx_render.py --scene assets/origami_20x20.usda
else
  echo "OV packages are not installed yet; skipped GPU physics and RTX render."
fi
