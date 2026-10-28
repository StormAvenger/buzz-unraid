# SPDX-License-Identifier: MIT
"""Build-time GUI, decoder, and persistence checks; no GPU or downloads needed."""
import os
from pathlib import Path
import tempfile
import wave

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
    from faster_whisper.audio import decode_audio
    for channels, rate in ((1, 16000), (2, 22050)):
        recording = Path(directory) / f"decoder-{channels}.wav"
        with wave.open(str(recording), "wb") as audio:
            audio.setnchannels(channels)
            audio.setsampwidth(2)
            audio.setframerate(rate)
            audio.writeframes(b"\x00\x00" * rate * channels)
        decoded = decode_audio(str(recording), split_stereo=channels == 2)
        streams = (decoded,) if channels == 1 else decoded
        assert all(len(stream) == 16000 for stream in streams), "Audio decoding/resampling failed"
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
    import buzz_observability
    buzz_observability.STATE = Path(directory) / 'readiness'
    buzz_observability.STATE.mkdir()
    os.environ['BUZZ_CONTAINER_READINESS'] = '1'
    app = Application([])
    app.show_main_window()
    app.processEvents()
    assert app.window.isVisible(), "Buzz main window was not created"
    from PyQt6.QtTest import QTest
    assert not buzz_observability.ui_ready(os.getpid(), buzz_observability.STATE)[0]
    QTest.qWait(2200)
    assert buzz_observability.ui_ready(os.getpid(), buzz_observability.STATE)[0], 'Qt readiness heartbeat missing'
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

    # Reproduce the stranded live window with no microphone, then exercise the
    # same application shortcut sent by the browser toolbar (including focus).
    from unittest.mock import patch
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest
    from buzz.widgets.recording_transcriber_widget import RecordingTranscriberWidget
    from buzz.widgets.audio_devices_combo_box import AudioDevicesComboBox
    original_window, original_db = app.window, app.db
    with patch.object(AudioDevicesComboBox, "get_audio_devices", return_value=[]), \
            patch.object(AudioDevicesComboBox, "get_default_device_id", return_value=-1):
        for _ in range(2):
            live = RecordingTranscriberWidget(app.window, flags=Qt.WindowType.Window)
            live.show()
            live.activateWindow()
            live.transcription_text_box.setFocus()
            app.processEvents()
            assert live.isVisible() and live.selected_device_id == -1
            QTest.keyClick(live.transcription_text_box, Qt.Key.Key_Home,
                           Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)
            app.processEvents()
            assert not live.isVisible(), "Home shortcut did not leave live recording"
            assert app.window is original_window and app.db is original_db
            assert app.window.isVisible(), "Home shortcut did not restore the main page"
            assert live.recording_amplitude_listener is None
    # It is also safe to press the button again while already on the main page.
    QTest.keyClick(app.window, Qt.Key.Key_Home,
                   Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)
    app.processEvents()
    assert app.window is original_window and app.window.isVisible()
    app.window.close()
    app.quit()
    print("Buzz main window, live-window return, audio decoding/resampling, and persistent preferences: passed")
