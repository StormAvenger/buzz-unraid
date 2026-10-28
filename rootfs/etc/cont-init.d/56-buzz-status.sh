#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
mkdir -p /dev/shm/buzz-status
chown "${USER_ID}:${GROUP_ID}" /dev/shm/buzz-status
chmod 755 /dev/shm/buzz-status
rm -f /dev/shm/buzz-status/heartbeat.json /dev/shm/buzz-status/public.json
