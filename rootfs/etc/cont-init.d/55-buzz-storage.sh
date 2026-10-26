#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
set -eu
mkdir -p /config/cache/buzz/models /config/cache/huggingface /config/cache/torch \
    /config/xdg/state /uploads /output
# Initialize only an empty dedicated upload/output directory. Never recursively
# change ownership of a user's media share. /config is managed by the GUI base.
for buzz_directory in /uploads /output; do
    if [ -z "$(find "$buzz_directory" -mindepth 1 -maxdepth 1 -print -quit)" ]; then
        chown "${USER_ID}:${GROUP_ID}" "$buzz_directory"
    fi
done
