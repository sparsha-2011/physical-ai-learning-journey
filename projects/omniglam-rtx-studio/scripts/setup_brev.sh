#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_version="${OMNIGLAM_PYTHON_VERSION:-3.10}"
uv_bin="${HOME}/.local/bin/uv"

cd "${project_dir}"

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "nvidia-smi was not found. Run this project on a GPU-backed Brev instance." >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm was not found. Install Node.js 20 or newer, then rerun this script." >&2
  exit 1
fi

if [[ ! -x "${uv_bin}" ]]; then
  python3 -m pip install --user uv
fi

"${uv_bin}" python install "${python_version}"

if [[ ! -x .venv/bin/python ]]; then
  "${uv_bin}" venv --python "${python_version}" .venv
fi
"${uv_bin}" pip install --python .venv/bin/python \
  ovrtx==0.4.0.346409 \
  ovstage==0.1.0.346039 \
  pillow==12.3.0 \
  numpy==2.2.6

if [[ ! -x .venv-physx/bin/python ]]; then
  "${uv_bin}" venv --python "${python_version}" .venv-physx
fi
"${uv_bin}" pip install --python .venv-physx/bin/python \
  ovphysx==0.5.9 \
  ovstage==0.1.0.346039 \
  numpy==2.2.6

npm ci
npm run build

echo
echo "Setup complete. Start the services with: npm run brev:start"
