#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check the release allowlist for accidental local data and credentials."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from importlib import util
spec = util.spec_from_file_location("package_source", ROOT / "scripts/package.py")
package = util.module_from_spec(spec)
spec.loader.exec_module(package)


def main():
    files = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    failures = []
    for name in filter(None, files):
        path = Path(name)
        allowed = name in package.FILES or path.parts[0] in package.DIRECTORIES
        if not allowed or path.name.endswith(".local.md") or any(p in path.parts for p in (".aws", "data", "__pycache__")):
            failures.append(f"{name}: outside public source allowlist")
            continue
        source = (ROOT / path).read_text(errors="replace")
        if path.suffix == ".lock":
            # Four-part package versions are not network addresses.
            source = re.sub(r"(?m)^([A-Za-z0-9_.-]+)==\S+", r"\1==VERSION", source)
        # Values are constructed so the scanner does not flag its own patterns.
        patterns = {
            "private network address": r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b",
            "personal filesystem path": r"/(?:Users|home)/[A-Za-z][^/\s]+/",
            "private key": "-----BEGIN " + r"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            "GitHub credential": "(?:gh" + r"p_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{25,})",
            "AWS access key": "AK" + r"IA[A-Z0-9]{16}",
        }
        for description, pattern in patterns.items():
            if re.search(pattern, source):
                failures.append(f"{name}: possible {description}")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"PASS: {len(list(filter(None, files)))} tracked source files; no local data or credential patterns found")


if __name__ == "__main__":
    main()
