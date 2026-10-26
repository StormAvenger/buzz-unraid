# SPDX-License-Identifier: GPL-3.0-only
"""Host-side checks for compatibility changes and container readiness detection."""
import contextlib
import importlib.util
import io
import re
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


compat = load("compat", "scripts/patch-buzz.py")
health = load("health", "rootfs/opt/buzz/healthcheck.py")


class CompatibilityTests(unittest.TestCase):
    def fixture(self, root):
        for relative, old, _ in compat.PATCHES:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(old + "\n")

    def test_upstream_drift_does_not_partially_patch_installation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            (root / compat.PATCHES[-1][0]).write_text("upstream changed\n")
            before = {p: p.read_bytes() for p in root.rglob("*.py")}
            with self.assertRaises(ValueError):
                compat.patch(root)
            self.assertEqual(before, {p: p.read_bytes() for p in root.rglob("*.py")})

    def test_compute_selection_for_cpu_pascal_and_modern_gpu(self):
        source = compat.PATCHES[0][2]
        for device, supported, expected in [
            ("cpu", set(), "int8"),
            ("auto", {"float32", "int8_float32"}, "int8_float32"),
            ("auto", {"int8_float16", "int8_float32"}, "int8_float16"),
        ]:
            with self.subTest(device=device, supported=supported):
                fake = types.SimpleNamespace(get_supported_compute_types=lambda device: supported)
                with patch.dict("sys.modules", {"ctranslate2": fake}):
                    namespace = {"device": device}
                    exec(source, namespace)
                self.assertEqual(namespace["compute_type"], expected)

    def test_output_directory_precedence(self):
        import os
        source = compat.PATCHES[-1][2]
        for explicit, environment, expected in [
            (None, "/output", "/output"),
            ("/custom", "/output", "/custom"),
            (None, "", "/input"),
        ]:
            namespace = {"os": os, "output_directory": explicit, "file_path": "/input/test.wav"}
            with patch.dict(os.environ, {"BUZZ_OUTPUT_DIRECTORY": environment}):
                exec(source, namespace)
            self.assertEqual(namespace["output_directory"], expected)

    def test_plugin_installer_cannot_mutate_default_container(self):
        import os
        replacement = next(new for relative, _, new in compat.PATCHES if relative == "buzz/pip_utils.py")
        namespace = {"os": os, "get_pip_cmd": lambda: self.fail("Package installer was invoked")}
        exec("def install(packages):\n" + replacement + "\n    return cmd", namespace)
        with patch.dict(os.environ, {"BUZZ_CONTAINER_ALLOW_PACKAGE_INSTALLS": "false"}):
            self.assertIsNone(namespace["install"]([]))
            with self.assertRaisesRegex(RuntimeError, "build time"):
                namespace["install"](["optional-plugin-dependency"])


class HealthTests(unittest.TestCase):
    def response(self, status=200):
        return contextlib.nullcontext(types.SimpleNamespace(status=status))

    def test_requires_both_browser_and_buzz(self):
        process = types.SimpleNamespace(read_bytes=lambda: b"/opt/venv/bin/python\0-m\0buzz\0")
        with patch.object(health, "urlopen", return_value=self.response()), patch.object(health.Path, "glob", return_value=[process]):
            health.main()

    def test_web_server_alone_is_not_healthy(self):
        process = types.SimpleNamespace(read_bytes=lambda: b"nginx\0")
        with patch.object(health, "urlopen", return_value=self.response()), patch.object(health.Path, "glob", return_value=[process]):
            with self.assertRaisesRegex(RuntimeError, "not running"):
                health.main()

    def test_web_failure_is_not_healthy(self):
        with patch.object(health, "urlopen", return_value=self.response(503)):
            with self.assertRaisesRegex(RuntimeError, "503"):
                health.main()

    def test_process_exit_race_is_tolerated(self):
        exited = types.SimpleNamespace(read_bytes=lambda: (_ for _ in ()).throw(FileNotFoundError()))
        process = types.SimpleNamespace(read_bytes=lambda: b"python\0-m\0buzz\0")
        with patch.object(health, "urlopen", return_value=self.response()), patch.object(health.Path, "glob", return_value=[exited, process]):
            health.main()


class UnraidTemplateTests(unittest.TestCase):
    def test_safe_storage_and_web_shortcut(self):
        root = ET.parse(ROOT / "templates/buzz.xml").getroot()
        self.assertEqual(root.findtext("WebUI"), "http://[IP]:[PORT:5800]/")
        self.assertEqual(root.findtext("Privileged"), "false")
        mappings = {entry.attrib["Target"]: entry.attrib for entry in root.findall("Config")}
        self.assertEqual(mappings["/input"]["Mode"], "ro")
        for target in ("/config", "/uploads", "/output"):
            self.assertEqual(mappings[target]["Mode"], "rw")
        self.assertEqual(mappings["USER_ID"]["Default"], "99")
        self.assertEqual(mappings["GROUP_ID"]["Default"], "100")


class DependencyLockTests(unittest.TestCase):
    def test_direct_wheel_urls_have_one_artifact_hash(self):
        # uv rejects multiple archive hashes on one direct URL. This can happen
        # when an index-based lock is reused while switching to a fixed wheel.
        source = (ROOT / "requirements/runtime.lock").read_text()
        blocks = re.split(r"\n(?=[A-Za-z0-9])", source)
        direct = [block for block in blocks if re.match(r"^[\w.-]+ @ https://", block)]
        self.assertGreaterEqual(len(direct), 2)
        for block in direct:
            with self.subTest(requirement=block.splitlines()[0]):
                self.assertEqual(len(re.findall(r"--hash=sha256:", block)), 1)


if __name__ == "__main__":
    unittest.main()
