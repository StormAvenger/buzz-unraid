# Validation — October 27, 2026

## Tested configuration

- Unraid 7.3.4 (initial development tests used 7.3.3); Ryzen 7 1800X.
- NVIDIA GTX 1080, 8192 MiB, with the Unraid NVIDIA Driver plugin.
- Buzz 1.4.5; Python 3.12; PyTorch 2.8.0+cu126; Faster Whisper 1.2.1; CTranslate2 4.6.2.

## Completed

- Host tests cover precision selection, export routing, upstream patch drift, browser/application health, process exit races, Unraid mappings, direct-wheel hash structure, and blocked runtime package installation.
- All six guarded compatibility changes apply to the pinned Buzz/Faster Whisper packages, and modified Python files parse. Mono and stereo WAV decoding/resampling is exercised during the image build.
- Python/shell syntax and XML/YAML parsing pass. The runtime and build dependency locks include artifact hashes.
- The Linux image built on the Unraid server. The application check runs in the final runtime stage, including its shared Python library, without build-only libraries available.
- The disposable CPU smoke test passed: browser readiness, Buzz window creation, writable folders as UID 99/GID 100, and files surviving a restart.
- The Unraid template created a healthy `buzz` container; its WebUI action opened the browser desktop.
- Real CUDA matrix computation passed on the GTX 1080. CTranslate2 reports `float32`, `int8`, and `int8_float32` GPU compute types.
- A public Whisper test recording was uploaded using the browser file manager, imported in Buzz, and transcribed with Faster Whisper Small in approximately 10 seconds. Container logs reported CUDA 12.6. TXT/SRT/VTT files were created in the mapped output folder as `nobody:users`.
- Remote Resizing made the desktop fit the browser window.
- On Unraid 7.3.4, the browser toolbar opened the uploads folder and transcript folder directly. Chrome downloaded a completed TXT transcript successfully. Both a 32 KB WAV and an 8 MiB WAV uploaded through the top-bar picker with matching SHA-256 hashes on the server; progress was visible for the larger upload.
- Recreating the container with the toolbar image and existing folder mappings preserved the saved transcription history and output files. The replacement container became healthy.

The [GitHub Linux check](https://github.com/StormAvenger/buzz-unraid/actions/runs/40603537304) passed for release commit `c3cb6ebd072395c236ccf48b3d3e0ff3e2761d48`. All 16 host tests, Docker build-context privacy checks, Compose validation, the Linux amd64 image build, and the disposable CPU/browser/persistent-storage smoke test passed on the hosted Ubuntu runner. GPU inference was verified separately on the Unraid server, using a cached Small model and the public JFK sample with networking disabled.

The [publication workflow](https://github.com/StormAvenger/buzz-unraid/actions/runs/40604201378) completed the clean-image inventory and matching-source collection: 285 Python packages, 330 Ubuntu packages, and 1,064 source archives with no collection failures. Its Trivy report contained no HIGH or CRITICAL findings; 645 MEDIUM and 32 LOW findings remain visible in the report. This is a point-in-time scan, not a guarantee that the image has no vulnerabilities. The matching [release assets](https://github.com/StormAvenger/buzz-unraid/releases/tag/v0.1.0) are public.

The official Community Applications scan passed: one valid Docker app, no hard errors or template warnings, and a publicly pullable image. The submission was sent and auto-approved on October 27, 2026. Catalog visibility awaits the next Community Applications build.

v0.1.0 image digest (the initial stable release): `sha256:60479faefdfd217d387446d69fbbab997fbf3fda8110626835dd1c2acab3da55`.

An anonymous pull using an empty Docker credential configuration succeeded on the Unraid server and matched that digest. The exact published image passed CUDA computation and offline Faster Whisper Small inference on the GTX 1080. The existing installation was switched to the public stable tag with its original storage mappings; it became healthy and the browser desktop retained its saved history. Unraid's Auto Update Applications plugin recognizes the public image and retains the selected-container update schedule.

## v0.1.1 navigation update

Release commit `3dd353e8b0afe180e0daab72e8daca8cc7d6089f` passed the [Linux build and browser/persistence check](https://github.com/StormAvenger/buzz-unraid/actions/runs/40634485673). The build exercises the real live-recording window with no microphone, uses the application shortcut from text-field focus, repeats the return, and verifies the same main-window and database objects remain open. The 16 host tests and JavaScript syntax check also passed.

Chrome testing opened Live Recording and returned to the main file list using **Back to main page** in the top bar, including repeated use. Testing used a disposable desktop with fresh application data. No personal recordings were used, and this release does not add browser microphone forwarding.

The [v0.1.1 publication workflow](https://github.com/StormAvenger/buzz-unraid/actions/runs/40635167113) repeats the image build, runtime checks, clean-image inventory, scan gate, and matching-source collection before publication. The CUDA/PyTorch dependency versions are unchanged.

The v0.1.1 release scan reports zero HIGH or CRITICAL findings, with 645 MEDIUM and 32 LOW findings retained in the report. Matching-source collection completed with 1,064 archives and no failures. The image labels identify version `0.1.1` and the tested commit above. Reports and sources are attached to the [matching release](https://github.com/StormAvenger/buzz-unraid/releases/tag/v0.1.1).

Published v0.1.1 and stable `:latest` image digest: `sha256:4b5920b92d4b1b1ba770f5916a5a96ef2716864d6d9857fa4aa454e0a5b5b0af`.

An anonymous pull with an empty Docker credential configuration succeeded on Unraid and matched that digest. The exact published image passed CUDA computation and offline Faster Whisper Small transcription of a public speech sample on the GTX 1080. A separate disposable container became healthy, reported version `0.1.1` and the release commit, and passed the Chrome live-recording-to-main-page button check with fresh application data. Both test containers were removed after verification. The production application was not reinstalled; installation is left to the user.

## Startup and diagnostics development checks

Runtime commit `55657a92003ffc0f096f72cdb7446a0886cabea9` passed the [Linux build and container checks](https://github.com/StormAvenger/buzz-unraid/actions/runs/40696129809): source/privacy checks, 20 Python tests, two JavaScript diagnostic-schema tests, Compose validation, build-context exclusion, actual Qt readiness, and HTTP/storage/restart smoke checks. This is development work for the next release; the stable image remains v0.1.1 until a separate publication workflow completes.

A disposable Unraid container built over v0.1.1 with the new status code and original pinned GUI assets showed the startup screen and then the live Buzz desktop. The GTX 1080 passed the new small CUDA computation and Faster Whisper capability probe, and the toolbar displayed GPU available. A browser diagnostic download contained only the declared version/status/event schema. A simulated paused application event loop triggered delayed-start guidance and the retry button; retry reconnected the browser, and the screen recovered automatically after the application resumed. No personal recordings, production appdata, or production container were used for these tests.

## Still unverified or unpublished

- Browser media playback.
- An ordinary source-file transcription through the read-only `/input` mapping (the completed UI transcription used `/uploads`).
- Database-changing upgrades/rollback and server reboot/autostart behavior.
- Larger models, other GPUs, speaker identification, speech separation, watched folders, and microphone forwarding.
- Community Applications catalog visibility after its next build (submission is approved).

No personal recordings were used for the verified sample. This report describes one working configuration and does not imply all Buzz features or GPU families have been tested.
