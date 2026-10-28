#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Small, fail-closed compatibility changes to Buzz and its pinned decoder."""
import argparse
from pathlib import Path

PATCHES = (
    (
        "buzz/transcriber/whisper_file_transcriber.py",
        'compute_type = "int8" if device == "cpu" else "int8_float16"',
        # Explicit FP16 fails on Pascal; let CT2 choose from the supported types.
        'compute_type = "int8" if device == "cpu" else ('
        '"int8_float16" if "int8_float16" in '
        '__import__("ctranslate2").get_supported_compute_types("cuda") '
        'else "int8_float32")',
    ),
    (
        "buzz/transcriber/recording_transcriber.py",
        'compute_type = "int8" if device == "cpu" else "int8_float16"',
        'compute_type = "int8" if device == "cpu" else ('
        '"int8_float16" if "int8_float16" in '
        '__import__("ctranslate2").get_supported_compute_types("cuda") '
        'else "int8_float32")',
    ),
    (
        "buzz/plugins/manager.py",
        "                    self._install_deps_if_needed(plugin)",
        "                    if self.enabled.get(plugin.metadata.id, False):\n"
        "                        self._install_deps_if_needed(plugin)",
    ),
    (
        "buzz/pip_utils.py",
        "    if not packages:\n        return\n\n    cmd = get_pip_cmd()",
        "    if not packages:\n        return\n\n"
        "    if os.getenv(\"BUZZ_CONTAINER_ALLOW_PACKAGE_INSTALLS\", \"false\") != \"true\":\n"
        "        raise RuntimeError(\"This container manages packages at build time. \"\n"
        "                           \"Add the plugin dependencies to the image and rebuild.\")\n\n"
        "    cmd = get_pip_cmd()",
    ),
    (
        "faster_whisper/audio.py",
        'av.open(input_file, mode="r", metadata_errors="ignore")',
        # PyAV 19 removed this keyword; metadata handling is now internal.
        'av.open(input_file, mode="r")',
    ),
    (
        "buzz/widgets/application.py",
        "        self.window = MainWindow(transcription_service)",
        "        self.window = MainWindow(transcription_service)\n\n"
        "        from PyQt6.QtGui import QKeySequence, QShortcut\n"
        "        self._container_home_shortcut = QShortcut(\n"
        "            QKeySequence(\"Ctrl+Alt+Home\"), self.window)\n"
        "        self._container_home_shortcut.setContext(\n"
        "            Qt.ShortcutContext.ApplicationShortcut)\n"
        "        self._container_home_shortcut.activated.connect(\n"
        "            self.return_to_main_window)",
    ),
    (
        "buzz/widgets/application.py",
        "    def show_main_window(self):",
        "    def return_to_main_window(self):\n"
        "        from buzz.widgets.recording_transcriber_widget import RecordingTranscriberWidget\n"
        "        # Use the recording window's normal stop/cleanup path. File jobs\n"
        "        # and the main application's database remain in the same process.\n"
        "        for window in self.topLevelWidgets():\n"
        "            if isinstance(window, RecordingTranscriberWidget) and window.isVisible():\n"
        "                window.close()\n"
        "        self.window.show()\n"
        "        self.window.raise_()\n"
        "        self.window.activateWindow()\n\n"
        "    def show_main_window(self):",
    ),
    (
        "buzz/transcriber/transcriber.py",
        'output_directory = output_directory or os.path.dirname(file_path)',
        'output_directory = output_directory or os.getenv("BUZZ_OUTPUT_DIRECTORY") '
        'or os.path.dirname(file_path)',
    ),
)


def patch(root: Path) -> None:
    changes = {}
    for relative, old, new in PATCHES:
        path = root / relative
        source = changes.get(path, path.read_text())
        if source.count(old) != 1:
            raise ValueError(f"Expected exactly one patch location in {relative}; review upstream changes")
        changes[path] = source.replace(old, new)
    for path, source in changes.items():
        path.write_text(source)
        print(f"Applied container compatibility change: {path.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site_packages", type=Path)
    patch(parser.parse_args().site_packages)
