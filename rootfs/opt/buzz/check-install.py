# SPDX-License-Identifier: MIT
"""Build-time GUI, decoder, and persistence checks; no GPU or downloads needed."""
import os
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory(prefix="buzz-install-check-") as directory:
    for name, relative in {
        "HOME": "home", "XDG_CONFIG_HOME": "config", "XDG_DATA_HOME": "data",
        "XDG_CACHE_HOME": "cache", "XDG_STATE_HOME": "state",
        "BUZZ_MODEL_ROOT": "models", "HF_HOME": "hf", "TORCH_HOME": "torch",
    }.items():
        os.environ[name] = str(Path(directory) / relative)
        Path(os.environ[name]).mkdir(parents=True, exist_ok=True)
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["BUZZ_DISABLE_TELEMETRY"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["WANDB_MODE"] = "disabled"
    os.environ["WANDB_DISABLE_GIT"] = "true"

    import torch
    import torchaudio
    import torchcodec
    import ctranslate2
    import faster_whisper
    import hydra
    import lightning
    import fsspec.implementations.http
    import wandb
    assert not (Path(wandb.__file__).parent / "bin/wandb-core").exists()
    tracking = wandb.init(mode="disabled")
    assert tracking.disabled, "Experiment tracking must stay disabled"
    tracking.finish()
    from buzz.widgets.application import Application
    from PyQt6.QtCore import QSettings
    import runpy

    assert torch.version.cuda == "12.6", f"Wrong CUDA build: {torch.__version__}"
    app = Application([])
    app.show_main_window()
    app.processEvents()
    assert app.window.isVisible(), "Buzz main window was not created"
    seed = runpy.run_path("/opt/buzz/first-run.py")["seed"]
    settings = QSettings("Buzz", "")
    seed(settings)
    assert settings.value("file_transcriber/output_formats") == ["txt", "srt", "vtt"]
    settings.setValue("file-transcriber/last-import-folder", "/custom-input")
    seed(settings)
    assert settings.value("file-transcriber/last-import-folder") == "/custom-input"
    from buzz.widgets.preferences_dialog.models.file_transcription_preferences import FileTranscriptionPreferences
    from buzz.model_loader import ModelType
    from buzz.transcriber.transcriber import get_output_file_path, Task, OutputFormat
    settings.beginGroup("file_transcriber")
    preferences = FileTranscriptionPreferences.load(settings)
    settings.endGroup()
    assert preferences.model.model_type == ModelType.FASTER_WHISPER
    assert preferences.output_formats == {OutputFormat.TXT, OutputFormat.SRT, OutputFormat.VTT}
    os.environ["BUZZ_OUTPUT_DIRECTORY"] = str(Path(directory) / "output")
    arguments = dict(file_path="/input/sample.wav", task=Task.TRANSCRIBE,
                     language="en", model=preferences.model, output_format=OutputFormat.TXT)
    assert Path(get_output_file_path(**arguments)).parent == Path(os.environ["BUZZ_OUTPUT_DIRECTORY"])
    assert Path(get_output_file_path(**arguments, output_directory="/explicit")).parent == Path("/explicit")
    app.window.close()
    app.quit()
    print("Buzz main window, decoder imports, and persistent preferences: passed")
