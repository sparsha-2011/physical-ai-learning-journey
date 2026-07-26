#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="${project_dir}/.venv-physx/bin/python"
system_libstdcpp="/usr/lib/x86_64-linux-gnu/libstdc++.so.6"

if [[ ! -x "${python_bin}" ]]; then
  echo "Missing ${python_bin}. Install ovphysx in the isolated environment first." >&2
    exit 1
fi

site_packages="$("${python_bin}" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
export LD_LIBRARY_PATH="${site_packages}/ovstage/bin:${site_packages}/ovstage/bin/plugins${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
if [[ -f "${system_libstdcpp}" ]]; then
  export LD_PRELOAD="${system_libstdcpp}${LD_PRELOAD:+:${LD_PRELOAD}}"
fi

exec "${python_bin}" "${project_dir}/server/ovphysx_bridge.py"
