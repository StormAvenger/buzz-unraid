#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
# Set the loader path BEFORE starting Python, including its spawned workers.
. /opt/buzz/library-paths.sh
/opt/venv/bin/python /opt/buzz/first-run.py
printf '%s\n' '[Buzz container] Opening Buzz. GPU verification: run python /opt/buzz/gpu-check.py in this container.'
cd /uploads
exec /opt/venv/bin/python -m buzz
