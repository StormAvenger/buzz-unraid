# Maintenance decisions

## Keep the existing application

The browser runs a remote desktop for Buzz, using jlesage/baseimage-gui. We do not maintain a replacement frontend, API, or job database. The base supplies the window manager, web server, file manager, audio bridge, user switching, and startup supervision. The main application runs as USER_ID/GROUP_ID. The base's service supervisor initializes as root; this is not a fully rootless image.

The container provides the virtual display in software. CUDA is used for inference and does not require passing through a physical display, an X socket, or a whole GPU to a VM. No privileged mode or Docker socket is required.

## Version pins

- GUI base: `jlesage/baseimage-gui:ubuntu-24.04-v4.14.0`.
- Build tool: `ghcr.io/astral-sh/uv:0.13.5`.
- Buzz: published Linux wheel `1.4.5`, including bundled Whisper.cpp and Demucs code.
- Python: Ubuntu 24.04's Python 3.12, matching that Buzz wheel.
- PyTorch/torchaudio: `2.8.0+cu126` via explicit official wheel URLs.
- Faster Whisper: `1.2.1`; CTranslate2: `4.6.2`; NumPy: `1.26.4`.
- All Python runtime dependencies are version-and-hash locked for Linux x86_64/glibc 2.39. Build bootstrap dependencies are locked separately.

OS packages still follow Ubuntu security updates when an image is rebuilt. Container bases use fixed release tags rather than immutable digests at this stage. Resolve and record registry digests before publishing a validated release; this project does not claim byte-identical image builds.

Regenerate locks with uv 0.13.5 and `sh scripts/lock-dependencies.sh`. Review the changes before rebuilding; no startup-time dependency installs are configured.

## Deliberate compatibility exception

Buzz 1.4.5's metadata declares `torch==2.8.0` and `torchcodec>=0.9.0`. TorchCodec's official compatibility table pairs PyTorch 2.8 with TorchCodec 0.7. The resolver override in `requirements/overrides.in` installs `torchcodec==0.7.0`; `--no-deps` installs the complete resolved lock without re-resolving Buzz's incompatible lower bound. Package metadata is retained, so generic `pip check`/`uv pip check` may report this known disagreement. Do not treat a clean dependency resolution alone as proof of runtime compatibility. The build explicitly imports TorchCodec and creates the Buzz window, and these checks must pass before deployment. Other workflows, especially speaker identification and newer Hugging Face models, need separate testing.

Sources:

- [Buzz 1.4.5 dependency metadata](https://github.com/chidiwilliams/buzz/blob/v1.4.5/pyproject.toml)
- [TorchCodec compatibility table](https://github.com/meta-pytorch/torchcodec/tree/v0.9.0#installing-torchcodec)
- [PyTorch Pascal support in CUDA 12.6 builds](https://dev-discuss.pytorch.org/t/cuda-toolkit-version-and-architecture-support-update-maxwell-and-pascal-architecture-support-removed-in-cuda-12-8-and-12-9-builds/3128)
- [CTranslate2 compute-type support](https://opennmt.net/CTranslate2/quantization.html)
- [cuDNN 9.10.2 support matrix](https://docs.nvidia.com/deeplearning/cudnn/backend/v9.10.2/reference/support-matrix.html)
- [GUI base documentation](https://github.com/jlesage/docker-baseimage-gui)

## Five narrow source changes

`scripts/patch-buzz.py` edits the installed pinned wheel in five places:

1. File Faster Whisper inference: choose supported INT8 precision rather than requesting unsupported FP16 on Pascal.
2. Recording Faster Whisper inference: same selection. Browser microphone forwarding is still outside this version's scope.
3. Plugin discovery: disabled plugins do not trigger package installation.
4. Runtime package installation: plugin dependencies must be included in the image and rebuilt. The explicit `BUZZ_CONTAINER_ALLOW_PACKAGE_INSTALLS=true` override is unsupported for the standard deployment and forfeits the locked-dependency guarantee.
5. Default export routing: use BUZZ_OUTPUT_DIRECTORY if a task has no explicit output directory. Explicit task destinations retain precedence.

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

The normal GitHub workflow builds and tests only. A separate, manually dispatched Publish image workflow builds, smoke-tests, and pushes versioned images to GHCR using the temporary repository token. It is not run by ordinary commits. See PUBLISHING.md before the first public image release.
