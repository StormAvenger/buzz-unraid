#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Export installed-package metadata and notices from a CLEAN image only.

Never run this against a user's application-data directories. No environment,
hostname, recordings, preferences, or logs are collected.
"""
import argparse
import ctypes
import importlib.metadata as metadata
import json
from pathlib import Path
import re
import shutil
import subprocess


def copy_notice(source, destination):
    if source.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    packages = []
    for dist in sorted(metadata.distributions(), key=lambda d: d.metadata["Name"].lower()):
        name = dist.metadata["Name"]
        license_classifiers = [c for c in dist.metadata.get_all("Classifier", []) if c.startswith("License ::")]
        packages.append({
            "name": name, "version": dist.version,
            "license_expression": dist.metadata.get("License-Expression", ""),
            "license_summary": dist.metadata.get("License", "").splitlines()[0:1],
            "license_classifiers": license_classifiers,
            "project_urls": dist.metadata.get_all("Project-URL", []),
        })
        for entry in dist.files or []:
            # Installed distribution notices only; never traverse appdata.
            if re.search(r"(?i)(license|copying|copyright|notice)", str(entry)):
                source = Path(dist.locate_file(entry))
                if source.is_file() and source.stat().st_size < 20_000_000:
                    safe_name = str(entry).replace("../", "parent/")
                    copy_notice(source, output / "notices/python" / name / safe_name)
    rows = subprocess.check_output([
        "dpkg-query", "-W", "-f=${binary:Package}\t${Version}\t${source:Package}\t${source:Version}\n",
    ], text=True).splitlines()
    system = []
    for line in rows:
        name, version, source_name, source_version = line.split("\t")
        base_name = name.split(":")[0]
        copyright_file = Path("/usr/share/doc") / base_name / "copyright"
        copyright_text = copyright_file.read_text(errors="replace") if copyright_file.is_file() else ""
        system.append({"name": name, "version": version,
                       "source_name": source_name or base_name,
                       "source_version": source_version or version,
                       "copyleft_notice": bool(re.search(r"(?i)(GPL|General Public License|MPL)", copyright_text))})
        copy_notice(copyright_file, output / "notices/ubuntu" / base_name / "copyright")
    for path in Path("/usr/share/common-licenses").glob("*"):
        copy_notice(path, output / "notices/common" / path.name)
    for path in Path("/usr/share/buzz-container").rglob("*"):
        if path.is_file():
            copy_notice(path, output / "notices/container" / path.relative_to("/usr/share/buzz-container"))
    # The wheel's actual FFmpeg build, not the system ffmpeg executable.
    import av
    lib = next(Path("/opt/venv/lib/python3.12/site-packages/av.libs").glob("libavcodec*"))
    codec = ctypes.CDLL(str(lib))
    codec.avcodec_license.restype = ctypes.c_char_p
    codec.avcodec_configuration.restype = ctypes.c_char_p
    manifest = {
        "schema": 1, "python": packages, "ubuntu": system,
        "pyav": {"version": av.__version__, "libraries": av.library_versions,
                 "ffmpeg_license": codec.avcodec_license().decode(),
                 "ffmpeg_configuration": codec.avcodec_configuration().decode()},
        "collection": "Clean image package metadata and installed notices only; no host or application data.",
    }
    (output / "inventory.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"Collected {len(packages)} Python and {len(system)} Ubuntu package records")


if __name__ == "__main__":
    main()
