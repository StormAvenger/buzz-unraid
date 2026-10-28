#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""PRs verify published sources or collect sources for a new local dependency build."""
import json
from pathlib import Path
import subprocess
from dependency import approved, package_identity, dependency_key

reference = json.loads(Path('release-output/dependency-reference.json').read_text())
if reference['image'].startswith('buzz-unraid-deps:'):
    subprocess.run(['docker', 'builder', 'prune', '--all', '--force'], check=True)
    subprocess.run(['python3', 'scripts/collect-sources.py', 'dependency-output/inventory.json', 'dependency-output'], check=True)
else:
    _, inventory = approved(dependency_key())
    actual = json.loads(Path('dependency-output/inventory.json').read_text())
    if package_identity(actual) != package_identity(inventory):
        raise ValueError('Published dependency inventory mismatch')
