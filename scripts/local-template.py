#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate an Unraid template for an image built locally instead of GHCR."""
import argparse
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="buzz-unraid:0.1.1-dev")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    tree = ET.parse(root / "templates/buzz.xml")
    tree.getroot().find("Repository").text = args.image
    # Keep this generated development template independent of the public feed.
    tree.getroot().find("TemplateURL").text = ""
    ET.indent(tree, space="  ")
    tree.write(sys.stdout, encoding="unicode", xml_declaration=True)
