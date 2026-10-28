#!/bin/sh
# SPDX-License-Identifier: MIT
# Disposable CPU/browser integration test for a built Linux image.
set -eu
buzz_image=${1:-buzz-unraid:0.1.2-dev}
buzz_name="buzz-smoke-$$"
buzz_created=0
cleanup() {
    if [ "$buzz_created" = 1 ]; then
        docker logs "$buzz_name" > "${TMPDIR:-/tmp}/$buzz_name.log" 2>&1 || true
        docker rm -fv "$buzz_name" >/dev/null
    fi
}
trap cleanup EXIT INT TERM
# The anonymous /config mount is removed with this disposable container.
docker create --name "$buzz_name" --platform linux/amd64 \
    -p 127.0.0.1::5800 --shm-size=1g \
    -v /config -v /uploads -v /output \
    -e BUZZ_FORCE_CPU=true "$buzz_image" >/dev/null
buzz_created=1
docker start "$buzz_name" >/dev/null
buzz_attempt=0
while [ "$buzz_attempt" -lt 60 ]; do
    buzz_status=$(docker inspect --format '{{.State.Health.Status}}' "$buzz_name")
    if [ "$buzz_status" = healthy ]; then
        docker exec "$buzz_name" python -c '
import json
from urllib.request import urlopen
with urlopen("http://127.0.0.1:5800/buzz-status.json") as response:
    assert "no-store" in response.headers["Cache-Control"]
    report = json.load(response)
assert report["schema"] == 1 and report["desktop"] == "ready"
assert set(report) == {"schema", "image_version", "buzz_version", "desktop", "gpu", "cpu_mode", "uptime_seconds", "updated_at", "events"}
assert report["cpu_mode"] is True
assert report["gpu"]["state"] in {"checking", "unavailable", "failed", "timeout"}
with urlopen("http://127.0.0.1:5800/") as response:
    assert b"buzz-startup" in response.read()
'
        docker exec --user 99:100 "$buzz_name" python /opt/buzz/check-install.py
        docker exec --user 99:100 "$buzz_name" python -c \
            'from pathlib import Path; [ (Path(p)/"smoke.txt").write_text("persistent") for p in ("/config", "/uploads", "/output") ]'
        docker restart "$buzz_name" >/dev/null
        # Verify the mounted files survive a restart.
        docker exec "$buzz_name" python -c \
            'from pathlib import Path; assert all((Path(p)/"smoke.txt").read_text() == "persistent" for p in ("/config", "/uploads", "/output"))'
        printf '%s\n' 'PASS: browser readiness, Buzz startup, user writes and restart persistence'
        exit 0
    fi
    if [ "$(docker inspect --format '{{.State.Running}}' "$buzz_name")" != true ]; then
        break
    fi
    buzz_attempt=$((buzz_attempt + 1))
    sleep 5
done
docker logs --tail 100 "$buzz_name"
printf '%s\n' 'FAIL: Buzz did not become healthy' >&2
exit 1
