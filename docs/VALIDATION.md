# Validation — October 26, 2026

## Tested configuration

- Unraid 7.3.3; Ryzen 7 1800X (owner-reported).
- NVIDIA GTX 1080, 8192 MiB; installed driver 580.178.04.
- Buzz 1.4.5; Python 3.12; PyTorch 2.8.0+cu126; Faster Whisper 1.2.1; CTranslate2 4.6.2.

## Completed

- Ten host tests cover precision selection, export routing, upstream patch drift, browser/application health, process exit races, Unraid mappings, direct-wheel hash structure, and blocked runtime package installation.
- All five changes apply to the published Buzz Linux wheel, and modified Python files parse.
- Python/shell syntax and XML/YAML parsing pass. The runtime and build dependency locks include artifact hashes.
- The Linux image built on the Unraid server. The application check runs in the final runtime stage, including its shared Python library, without build-only libraries available.
- The disposable CPU smoke test passed: browser readiness, Buzz window creation, writable folders as UID 99/GID 100, and files surviving a restart.
- The Unraid template created a healthy `buzz` container; its WebUI action opened the browser desktop.
- Real CUDA matrix computation passed on the GTX 1080. CTranslate2 reports `float32`, `int8`, and `int8_float32` GPU compute types.
- A public Whisper test recording was uploaded using the browser file manager, imported in Buzz, and transcribed with Faster Whisper Small in approximately 10 seconds. Container logs reported CUDA 12.6. TXT/SRT/VTT files were created in the mapped output folder as `nobody:users`.
- Remote Resizing made the desktop fit the browser window.

The [GitHub Linux check](https://github.com/StormAvenger/buzz-unraid/actions/runs/40421887408) passed for commit `d0fbdb7e1f926b988ce6557fc25c43e2f233c8a1`, including the repository licensing, artwork, and publication metadata. Source tests, Compose validation, the Linux amd64 image build, and the disposable CPU/browser/persistent-storage smoke test all passed on the hosted Ubuntu runner. GPU inference was verified separately on the Unraid server.

## Still unverified or unpublished

- Browser transcript downloads and media playback.
- An ordinary source-file transcription through the read-only `/input` mapping (the completed UI transcription used `/uploads`).
- Container recreation with existing appdata, upgrades/rollback, and server reboot/autostart behavior. Restart persistence passed; recreation is a distinct check.
- Larger models, other GPUs, speaker identification, speech separation, watched folders, and microphone forwarding.
- A complete bundled-license/corresponding-source inventory and container image scan.
- Public registry image availability and Community Applications acceptance.

No personal recordings were used for the verified sample. This report describes one working configuration and does not imply all Buzz features or GPU families have been tested.
