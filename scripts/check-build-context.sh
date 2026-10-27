#!/bin/sh
# SPDX-License-Identifier: MIT
# Exercise Docker's own ignore matching with harmless nested sentinel files.
set -eu
buzz_root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
buzz_context=$(mktemp -d)
trap 'rm -rf "$buzz_context"' EXIT INT TERM
mkdir -p "$buzz_context/source/rootfs/nested/__pycache__" "$buzz_context/source/docs"
cp "$buzz_root/.dockerignore" "$buzz_context/source/.dockerignore"
for buzz_path in rootfs/nested/.env rootfs/nested/.env.private \
    rootfs/nested/.DS_Store rootfs/nested/private.local.md \
    rootfs/nested/__pycache__/sentinel.pyc docs/private.local.md; do
    printf '%s\n' 'DO-NOT-INCLUDE' > "$buzz_context/source/$buzz_path"
done
printf '%s\n' 'PUBLIC-EXAMPLE' > "$buzz_context/source/.env.example"
printf '%s\n' 'SOURCE' > "$buzz_context/source/rootfs/nested/keep.py"
printf '%s\n' 'FROM scratch' 'COPY . /' > "$buzz_context/source/Dockerfile"
docker build --quiet --output "type=local,dest=$buzz_context/output" "$buzz_context/source"
test -f "$buzz_context/output/rootfs/nested/keep.py"
test -f "$buzz_context/output/.env.example"
if find "$buzz_context/output" -type f -exec cat {} + | grep -q DO-NOT-INCLUDE; then
    printf '%s\n' 'FAIL: private/cache files entered the Docker build context' >&2
    exit 1
fi
printf '%s\n' 'PASS: Docker excludes nested private files and caches, preserving source and the public example'
