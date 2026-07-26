#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="${project_dir}/.venv/bin/python"
shared_python="${project_dir}/../omniverse-sensor-lab/.venv/bin/python"
system_libstdcpp="/usr/lib/x86_64-linux-gnu/libstdc++.so.6"

if [[ ! -x "${python_bin}" && -x "${shared_python}" ]]; then
  python_bin="${shared_python}"
fi

if [[ ! -x "${python_bin}" ]]; then
  echo "Missing an ovrtx Python environment. Follow the install steps in README.md." >&2
  exit 1
fi

# A venv created from Conda can inherit an older libstdc++. ovrtx 0.4 needs
# GLIBCXX_3.4.30; prefer Ubuntu's runtime when it is available.
if [[ -f "${system_libstdcpp}" ]]; then
  export LD_PRELOAD="${system_libstdcpp}${LD_PRELOAD:+:${LD_PRELOAD}}"
fi

exec "${python_bin}" "${project_dir}/server/ovrtx_bridge.py" --port 8791 --auto-start "$@"
