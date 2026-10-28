# Maintenance decisions

## Keep the existing application

The browser runs a remote desktop for Buzz, using jlesage/baseimage-gui. We do not maintain a replacement frontend, API, or job database. The base supplies the window manager, web server, file manager, audio bridge, user switching, and startup supervision. The main application runs as USER_ID/GROUP_ID. The base's service supervisor initializes as root; this is not a fully rootless image.

The small Buzz browser toolbar reuses the base's existing file manager and WebSocket service. `scripts/patch-web-ui.py` adds the toolbar assets to the page and extends the pinned file-manager module with an initial folder, a directory-ready event, and a guarded upload method. It validates every patch anchor before writing, so base changes fail the image build instead of silently breaking transfers. Uploads wait for the server to confirm `/uploads`; downloads open `/output`. The existing backend still enforces allowed paths, file permissions, and duplicate-name protection. No additional listening port or file-transfer service is added.

The top-bar **Back to main page** button uses the active noVNC desktop connection to send Ctrl+Alt+Home. A container-specific application shortcut closes visible live-recording windows through Buzz's normal cleanup path, then raises the existing main window. It does not restart Buzz or change the file-transcription queue/database. The toolbar imports the same versioned UI module as index.html so it shares the active connection. The build exercises actual keyboard navigation out of a live window with no microphone, repeated use, and preservation of the main window/database objects. Browser microphone forwarding remains outside this release.

The container provides the virtual display in software. CUDA is used for inference and does not require passing through a physical display, an X socket, or a whole GPU to a VM. No privileged mode or Docker socket is required.

## Startup status and private diagnostics

v0.1.2 adds a read-only `/buzz-status.json` snapshot to the existing web server, inheriting the desktop's optional authentication. It opens no new listening port. The snapshot is generated from an allowlist, never from raw logs, environment variables, media, file history, or exception strings. The browser constructs the diagnostic download from a second explicit allowlist and does not upload it anywhere.

A retained Qt timer writes a heartbeat only after the actual main window becomes visible and the event loop runs. The status monitor follows that application's process, checks heartbeat freshness, and performs a bounded CUDA/compute-type probe in a separate subprocess once per start. The browser requires both fresh application readiness and its active desktop connection before dismissing the startup screen. A GPU availability result describes compatibility, not which backend an individual job uses. CPU preference changes are picked up from the Qt heartbeat. Reports keep at most 40 status transitions, with relative seconds rather than private application log content.

The heartbeat and public snapshot live under `/dev/shm/buzz-status`, on Docker's shared-memory tmpfs. Their frequent updates do not write to the container's writable disk layer. The status endpoint also skips access-log entries so browser polling does not produce repeated disk writes; other web access/error logging remains unchanged. Startup recreates the directory with the application user/group ownership; nothing here needs persistence. The smoke test checks that both files are on the `/dev/shm` tmpfs and that the existing status URL still serves the snapshot. The template's existing shared-memory setting is sufficient; no new mapping is required.

The Docker healthcheck also requires the real window heartbeat. Build checks exercise the Qt timer, and the disposable smoke test checks the live HTTP snapshot. Host privacy tests inject unexpected fields and raw output to verify they cannot enter the downloaded report. Planned work is tracked in [ROADMAP.md](ROADMAP.md).

## Version pins

- GUI base: `jlesage/baseimage-gui:ubuntu-24.04-v4.14.0`.
- Build tool: `ghcr.io/astral-sh/uv:0.13.5`.
- Buzz: published Linux wheel `1.4.5`, including bundled Whisper.cpp and Demucs code.
- Python: Ubuntu 24.04's Python 3.12, matching that Buzz wheel.
- PyTorch/torchaudio: `2.8.0+cu126` via explicit official wheel URLs.
- Faster Whisper: `1.2.1`; CTranslate2: `4.6.2`; NumPy: `1.26.4`.
- All Python runtime dependencies are version-and-hash locked for Linux x86_64/glibc 2.39. Build bootstrap dependencies are locked separately.

OS packages still follow Ubuntu security updates when an image is rebuilt. The GUI base and uv build-tool images are pinned to immutable registry digests. Ubuntu packages still depend on the repositories at build time; this project does not claim byte-identical image builds.

Regenerate locks with uv 0.13.5 and `sh scripts/lock-dependencies.sh`. Review the changes before rebuilding; no startup-time dependency installs are configured.

## Deliberate compatibility overrides

Buzz 1.4.5's metadata declares `torch==2.8.0` and `torchcodec>=0.9.0`. TorchCodec's official compatibility table pairs PyTorch 2.8 with TorchCodec 0.7. The resolver override in `requirements/cu126/overrides.in` installs `torchcodec==0.7.0`; `--no-deps` installs the complete resolved lock without re-resolving Buzz's incompatible lower bound. Package metadata is retained, so generic `pip check`/`uv pip check` may report this known disagreement. Do not treat a clean dependency resolution alone as proof of runtime compatibility. The build explicitly imports TorchCodec and creates the Buzz window, and these checks must pass before deployment. Other workflows, especially speaker identification and newer Hugging Face models, need separate testing.

NeMo 2.8.0rc2 also pins fsspec 2024.12.0, Hydra <=1.3.2, and Lightning <=2.4.0. The release overrides these to fsspec[http] 2026.6.0, Hydra 1.3.8, and Lightning 2.6.6 to address the image scan's high-severity findings. The HTTP extra is explicit because replacing a dependency with an override can otherwise remove its extras. Setuptools 81.0.0 retains pkg_resources compatibility while updating vulnerable vendored tools; the bootstrap wheel version is 0.46.3. Build checks import the updated modules and create the real Buzz window. Faster Whisper remains the validated backend; NeMo transcription is not a supported/tested release claim. Keep these exceptions documented when evaluating generic metadata checks or updating the lock.

The installed W&B Python package remains available to satisfy upstream imports, but experiment tracking is disabled and its bundled tracking executables are removed in the builder before the runtime COPY. They are unnecessary for transcription, and the latest upstream wheel still bundles a Go runtime with a high-severity certificate-validation finding. Build checks verify the executable is absent and a disabled tracking run requires no service. Re-enable this feature only through a reviewed image rebuild with a fixed service.

The release workflow pins actions by their official repository commit SHAs and Trivy by the verified registry index digest. Checkout does not persist credentials. The image scan report is preserved, and publication stops on any HIGH or CRITICAL finding or a missing/invalid report. Lower-severity findings remain in the report for review. A Docker-based build-context check verifies that nested private notes, environment files, and Python caches are excluded.

Sources:

- [Buzz 1.4.5 dependency metadata](https://github.com/chidiwilliams/buzz/blob/v1.4.5/pyproject.toml)
- [TorchCodec compatibility table](https://github.com/meta-pytorch/torchcodec/tree/v0.9.0#installing-torchcodec)
- [PyTorch Pascal support in CUDA 12.6 builds](https://dev-discuss.pytorch.org/t/cuda-toolkit-version-and-architecture-support-update-maxwell-and-pascal-architecture-support-removed-in-cuda-12-8-and-12-9-builds/3128)
- [CTranslate2 compute-type support](https://opennmt.net/CTranslate2/quantization.html)
- [cuDNN 9.10.2 support matrix](https://docs.nvidia.com/deeplearning/cudnn/backend/v9.10.2/reference/support-matrix.html)
- [GUI base documentation](https://github.com/jlesage/docker-baseimage-gui)

## Narrow source changes

`scripts/patch-buzz.py` edits the pinned Buzz and Faster Whisper installations at eight guarded anchors:

1. File Faster Whisper inference: choose supported INT8 precision rather than requesting unsupported FP16 on Pascal.
2. Recording Faster Whisper inference: same selection. Browser microphone forwarding is still outside this version's scope.
3. Plugin discovery: disabled plugins do not trigger package installation.
4. Runtime package installation: plugin dependencies must be included in the image and rebuilt. The explicit `BUZZ_CONTAINER_ALLOW_PACKAGE_INSTALLS=true` override is unsupported for the standard deployment and forfeits the locked-dependency guarantee.
5. Default export routing: use BUZZ_OUTPUT_DIRECTORY if a task has no explicit output directory. Explicit task destinations retain precedence.
6. Faster Whisper audio decoding: remove the obsolete metadata_errors keyword that PyAV 19 no longer accepts. The build decodes mono/stereo WAV data and checks resampling, so decoder API changes are exercised without requiring a GPU.

7. Main-page navigation: install an application-wide Ctrl+Alt+Home shortcut and its return handler in Buzz's Application class (two anchors). Live recording uses its existing close/stop cleanup, while the main window and file jobs stay in place.

The patch checks that every target appears exactly once before writing anything. If upstream changes, the image build fails until reviewed. Host tests cover CPU/Pascal/modern-GPU compute selection, output precedence, blocked runtime package installation, direct-wheel lock hashes, and atomic failure on upstream drift. Full-window and preference tests run inside the image build. No other upstream application source is intentionally changed.

First-run seeding uses Buzz's QSettings API, its actual `file_transcriber` preference group, and its model dataclass. It fills missing settings individually and preserves user changes. Automatic export formats default to TXT/SRT/VTT.

## Release gates

1. Validate source and Compose configuration.
2. Build on Linux amd64; pass real-window/import/preference/export-routing checks.
3. Pass the disposable browser/startup/permissions/persistence smoke test.
4. On the actual Unraid server, run `gpu-check.py` with and without a spoken recording.
5. Through the browser UI, verify a read-only server file and an uploaded file transcribe, results download, media plays, and exports land in the mapped output share.
6. Replace/recreate the container with the same mappings and confirm settings/history/models/results remain usable. Restart-only testing is insufficient for this gate.
7. Check that the source files are unchanged, permission failures are understandable, closing the app restarts it, and an interrupted job does not silently appear complete.
8. Record image size, disk usage, VRAM, timing, hardware/driver details, and remaining limitations.
9. Verify bundled third-party licenses/source obligations and image scan results; pin base digests; publish a versioned image only after these gates pass.

The normal GitHub workflow builds and tests only. The Publish image workflow runs on published GitHub releases, builds and smoke-tests, collects clean-image notices/inventory and matching upstream source archives, scans the image, attaches release records, and pushes versioned images to GHCR using the temporary repository token. Ordinary commits do not publish images. Manual dispatch defaults to preparation without publishing. See PUBLISHING.md before the first public image release.
