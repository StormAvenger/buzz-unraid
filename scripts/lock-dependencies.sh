#!/bin/sh
# SPDX-License-Identifier: MIT
# Run with uv 0.13.5; source builds may need network access during resolution.
set -eu
cd "$(dirname "$0")/.."
uv pip compile requirements/cu126/build.in --python-version 3.12 \
    --python-platform x86_64-manylinux_2_39 --generate-hashes \
    --output-file requirements/cu126/build.lock
uv pip compile requirements/cu126/runtime.in --overrides requirements/cu126/overrides.in \
    --python-version 3.12 --python-platform x86_64-manylinux_2_39 \
    --generate-hashes --output-file requirements/cu126/runtime.lock
