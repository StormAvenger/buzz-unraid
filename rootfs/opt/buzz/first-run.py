# SPDX-License-Identifier: MIT
"""Seed missing preferences without resetting any existing user preferences."""
import os
from pathlib import Path

from PyQt6.QtCore import QSettings


def seed(settings):
    from buzz.model_loader import ModelType, TranscriptionModel, WhisperModelSize

    defaults = {
        "file-transcriber/last-import-folder": "/input",
        "file_transcriber/model": TranscriptionModel(
            model_type=ModelType.FASTER_WHISPER,
            whisper_model_size=WhisperModelSize.SMALL,
        ),
        "file_transcriber/output_formats": ["txt", "srt", "vtt"],
    }
    for key, value in defaults.items():
        if not settings.contains(key):
            settings.setValue(key, value)
    settings.sync()
    if settings.status() != QSettings.Status.NoError:
        raise RuntimeError("Could not save Buzz preferences. Check /config permissions.")


if __name__ == "__main__":
    for directory in ("/config", "/uploads", "/output"):
        if not os.access(directory, os.W_OK | os.X_OK):
            raise SystemExit(f"{directory} is not writable. Check USER_ID/GROUP_ID and the mapped folder permissions.")
    Path(os.environ["BUZZ_MODEL_ROOT"]).mkdir(parents=True, exist_ok=True)
    seed(QSettings("Buzz", ""))
