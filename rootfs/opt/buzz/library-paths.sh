# SPDX-License-Identifier: MIT
# Sourced by application and diagnostics launchers. Keep host driver paths too.
buzz_library_dirs=$(/opt/venv/bin/python -c 'import glob; print(":".join(sorted(glob.glob("/opt/venv/lib/python3.12/site-packages/nvidia/*/lib")) + ["/opt/venv/lib/python3.12/site-packages/torch/lib"]))')
export LD_LIBRARY_PATH="${buzz_library_dirs}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
unset buzz_library_dirs
