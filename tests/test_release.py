# SPDX-License-Identifier: MIT
"""Release source records must preserve integrity and stay inside their output."""
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sources", ROOT / "scripts/collect-sources.py")
sources = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sources)
scan_spec = importlib.util.spec_from_file_location("image_scan", ROOT / "scripts/check-image-scan.py")
image_scan = importlib.util.module_from_spec(scan_spec)
scan_spec.loader.exec_module(image_scan)


class SourceRecordsTests(unittest.TestCase):
    def test_split_archive_reassembles_without_data_loss(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            writer = sources.PartsWriter(target, limit=7)
            writer.write(b"12345")
            writer.write(b"678901234567890")
            writer.close()
            parts = sorted(target.iterdir())
            self.assertEqual([p.stat().st_size for p in parts], [7, 7, 6])
            self.assertEqual(b"".join(p.read_bytes() for p in parts), b"12345678901234567890")

    def test_notice_archive_cannot_traverse_output_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            archive = target / "source.tar"
            with tarfile.open(archive, "w") as bundle:
                entry = tarfile.TarInfo("../../COPYING")
                entry.size = 6
                bundle.addfile(entry, io.BytesIO(b"notice"))
            sources.source_notices(archive, target / "notices")
            self.assertEqual((target / "notices/COPYING").read_text(), "notice")
            self.assertFalse((target / "COPYING").exists())

    def test_download_rejects_wrong_source_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            response = io.BytesIO(b"different source")
            with patch.object(sources, "request", return_value=response):
                with self.assertRaisesRegex(ValueError, "hash mismatch"):
                    sources.download({"url": "https://example.org/source.tar.gz", "component": "example", "sha256": "0" * 64}, Path(directory))


class ImageScanTests(unittest.TestCase):
    def test_high_findings_block_even_without_a_published_fix(self):
        report = {"SchemaVersion": 2, "Results": [{"Vulnerabilities": [
            {"Severity": "HIGH", "VulnerabilityID": "CVE-example", "PkgName": "example", "InstalledVersion": "1.0"}
        ]}]}
        with self.assertRaisesRegex(ValueError, "CVE-example"):
            image_scan.check_report(report)

    def test_lower_severity_findings_stay_visible(self):
        report = {"SchemaVersion": 2, "Results": [{"Vulnerabilities": [
            {"Severity": "MEDIUM"}, {"Severity": "LOW"}
        ]}]}
        self.assertEqual(image_scan.check_report(report), {"LOW": 1, "MEDIUM": 1})

    def test_missing_scan_is_not_a_clean_scan(self):
        for report in ({}, {"SchemaVersion": 2, "Results": []}):
            with self.assertRaisesRegex(ValueError, "Missing"):
                image_scan.check_report(report)


if __name__ == "__main__":
    unittest.main()
