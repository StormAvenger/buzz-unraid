#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Stop publication on high/critical image findings or an invalid scan report."""
import argparse
from collections import Counter
import json
from pathlib import Path


def check_report(report):
    results = report.get("Results")
    if report.get("SchemaVersion") != 2 or not isinstance(results, list) or not results:
        raise ValueError("Missing or unsupported Trivy image report")
    counts = Counter()
    blocked = []
    for result in results:
        for finding in result.get("Vulnerabilities", []):
            severity = finding.get("Severity", "UNKNOWN")
            counts[severity] += 1
            if severity in ("HIGH", "CRITICAL"):
                blocked.append(f"{finding.get('VulnerabilityID')}: {finding.get('PkgName')} "
                               f"{finding.get('InstalledVersion')} ({severity})")
    if blocked:
        raise ValueError("Image publication blocked by scan findings:\n" + "\n".join(blocked))
    return dict(sorted(counts.items()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    print("Image scan severity counts:", check_report(json.loads(args.report.read_text())))
