#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Create a transfer archive from an explicit source allowlist, excluding local data."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "Dockerfile", "Dockerfile.deps", "README.md", "THIRD_PARTY_NOTICES.md", "compose.yaml",
    "compose.nvidia.yaml", ".env.example", ".dockerignore", ".gitignore",
    ".github/workflows/container.yml", ".github/workflows/dependencies.yml", ".github/workflows/publish-image.yml",
    "LICENSE", "icon.svg", "ca_profile.xml", "AGENTS.md", ".github/PULL_REQUEST_TEMPLATE.md",
)
DIRECTORIES = ("rootfs", "scripts", "requirements", "docs", "unraid", "tests", "licenses", "templates")

if __name__ == "__main__":
    paths = {ROOT / name for name in FILES}
    for name in DIRECTORIES:
        paths.update(p for p in (ROOT / name).rglob("*") if p.is_file()
                     and "__pycache__" not in p.parts and p.suffix != ".pyc"
                     and not p.name.endswith(".local.md") and p.name != ".DS_Store")
    output = ROOT / "Buzz-Unraid-starter.zip"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            archive.write(path, Path("buzz-unraid") / path.relative_to(ROOT))
    print(f"Created {output.name}: {len(paths)} source files, {output.stat().st_size:,} bytes")
