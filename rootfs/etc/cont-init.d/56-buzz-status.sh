#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
mkdir -p /tmp/buzz-status
chown "${USER_ID}:${GROUP_ID}" /tmp/buzz-status
chmod 755 /tmp/buzz-status
rm -f /tmp/buzz-status/heartbeat.json /tmp/buzz-status/public.json
