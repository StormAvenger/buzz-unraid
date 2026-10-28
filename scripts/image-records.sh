#!/bin/sh
# SPDX-License-Identifier: MIT
# Clean images only. No application-data mounts, environment dumps or raw logs.
set -eu
image=$1
output=$2
mkdir -p "$output"
docker run --rm --network none --user "$(id -u):$(id -g)" --entrypoint /opt/venv/bin/python \
    -v "$PWD/scripts/release-inventory.py:/inventory.py:ro" \
    -v "$PWD/$output:/release-output" "$image" /inventory.py /release-output
docker image inspect --format '{{json .Config.Labels}}' "$image" > "$output/image-labels.json"
docker image inspect --format '{{.Size}}' "$image" > "$output/image-bytes.txt"
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock:ro \
    -v "$PWD/$output:/reports" \
    ghcr.io/aquasecurity/trivy:0.76.1@sha256:790fd66d1697395d8693d1acaa1ea702406a20f109b6fc7bac8db623eca6c06c image \
    --scanners vuln --format json --output /reports/image-scan.json "$image"
python3 scripts/check-image-scan.py "$output/image-scan.json"
