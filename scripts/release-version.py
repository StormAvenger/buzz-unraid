#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Validate release tags and select mutable image channels from release metadata."""
import argparse
import json
from pathlib import Path
import re


def version(tag):
    match = re.fullmatch(r"v([0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*)?)", tag)
    if not match or len(match[1]) > 128:
        raise ValueError("Use a Docker-compatible release tag such as v1.2.3 or v1.2.3-rc.1")
    return match[1]


def channels(tag, release):
    value = version(tag)
    if (release.get("tagName") != tag or release.get("isDraft") is not False
            or type(release.get("isPrerelease")) is not bool):
        raise ValueError("Expected a published matching GitHub release with a prerelease flag")
    if release["isPrerelease"]:
        return ("beta",) if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+-(?:rc|beta)\.[0-9]+", value) else ()
    # Advance beta first: a failed beta push must not advance latest alone.
    return ("beta", "latest") if "-" not in value else ()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag")
    parser.add_argument("--release-json", type=Path)
    args = parser.parse_args()
    value = version(args.tag)
    selected = channels(args.tag, json.loads(args.release_json.read_text())) if args.release_json else None
    print(f"VERSION={value}")
    if selected is not None:
        print("CHANNEL_TAGS=" + " ".join(selected))


if __name__ == "__main__":
    main()
