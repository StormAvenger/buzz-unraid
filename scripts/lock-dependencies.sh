#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Run with uv 0.13.5; source builds may need network access during resolution.
set -eu
cd "$(dirname "$0")/.."
uv pip compile requirements/build.in --python-version 3.12 \
    --python-platform x86_64-manylinux_2_39 --generate-hashes \
    --output-file requirements/build.lock
uv pip compile requirements/runtime.in --overrides requirements/overrides.in \
    --python-version 3.12 --python-platform x86_64-manylinux_2_39 \
    --generate-hashes --output-file requirements/runtime.lock
