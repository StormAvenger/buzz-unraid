# Third-party software

Container-specific source, scripts, tests, configuration, original artwork, and documentation are Copyright (c) 2026 StormAvenger and licensed under MIT; see the root LICENSE. This does not replace upstream notices or third-party licenses.

This is an unofficial container for Buzz. It is not endorsed by the Buzz maintainers, Unraid, NVIDIA, or the GUI base maintainer.

- Buzz: https://github.com/chidiwilliams/buzz — MIT. Its license text is preserved in `licenses/Buzz-LICENSE` and in the installed wheel.
- jlesage GUI base: https://github.com/jlesage/docker-baseimage-gui — MIT for the base project; bundled components have their own licenses.
- Faster Whisper: https://github.com/SYSTRAN/faster-whisper — MIT.
- CTranslate2: https://github.com/OpenNMT/CTranslate2 — MIT.
- PyTorch, torchaudio, TorchCodec, Qt/PyQt, FFmpeg, Demucs and other dependencies retain their own license terms. Buzz's MIT license does not replace them.
- CUDA/cuDNN and NVIDIA runtime packages are subject to NVIDIA's applicable license terms.
- Downloaded model weights are separate artifacts with their own license terms. They are downloaded into appdata rather than included in this image by default.

The v0.1.0 release includes the clean-image package inventory, preserved notices, and matching source archives for redistributed components, including PyQt/Qt and FFmpeg. NVIDIA runtime handling and component-specific redistribution decisions are documented in [docs/REDISTRIBUTION.md](docs/REDISTRIBUTION.md). The complete image contains software under multiple licenses.

Published image releases include `inventory.json`, `source-manifest.json`, `notices.tar.gz`, source archive parts, and checksums as assets on the matching [GitHub release](https://github.com/StormAvenger/buzz-unraid/releases). `SOURCE-README.txt` explains how to extract the source parts. Installed package notices remain in the image, and `/usr/share/buzz-container/SOURCE-LOCATION.txt` identifies the matching release. These records cover dependency versions and notices; they are not a claim that every application feature or GPU has been tested.

Container-specific GPU, export, and plugin dependency changes to Buzz's installed Python files are documented in `docs/MAINTENANCE.md` and reproducibly applied by `scripts/patch-buzz.py`.
