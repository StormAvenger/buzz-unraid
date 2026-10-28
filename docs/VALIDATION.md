# Validation

This page describes the current checks and their limits. Release-specific commits, digests, scan counts, source records and hardware results belong in the [GitHub release notes](https://github.com/StormAvenger/buzz-unraid/releases).

## Required automated checks

Run `python3 scripts/check-public-files.py`, `python3 -m unittest discover -s tests -v`, and `node --test tests/test_status.mjs`. Validate Compose, the Docker build context, and guarded patches before building the Linux amd64 image. The image build runs `check-install.py` against the actual runtime: decoder imports/resampling, main window, Qt heartbeat, live-window return, preferences and export routing.

Run `sh scripts/smoke-test.sh IMAGE` with disposable anonymous data. It verifies HTTP readiness, shared-memory status files, user writes and restart persistence. Publication also requires a clean-image inventory/notices, a valid scan with no HIGH or CRITICAL findings, complete matching sources, and checksums. Retain lower-severity findings in the report.

## Hardware and browser verification

Use disposable containers and public fixtures. On supported NVIDIA hardware run `gpu-check.py`, including an offline transcription using an existing model and a public speech sample. Detection alone is insufficient: actual CUDA computation and inference must work. Test startup/reconnection guidance, GPU availability, transfers, the main-page return and the locally downloaded diagnostic schema. Verify file permissions, read-only inputs, export destinations and recreation with the same test mappings when applicable.

For a published image, verify anonymous access, version/revision labels, versioned/stable digests, source availability and record checksums. Delete only the test containers and their disposable volumes. Never use production appdata for inventories or publish raw test logs containing user data.

## Current compatibility and limits

The validated baseline is Buzz 1.4.5, Python 3.12, PyTorch 2.8.0+cu126, Faster Whisper 1.2.1 and CTranslate2 4.6.2 on Unraid with a GTX 1080. This is one tested configuration, not a claim for every GPU or Buzz backend.

Browser microphone forwarding is unconfigured. Browser audio playback, larger models/other GPU families, speaker identification, speech separation, watched folders, database-changing rollback and server reboot/autostart need separate verification. A GPU availability badge reports compatibility, not an individual job's backend. Health status does not itself restart an unhealthy container. Community Applications approval and catalog visibility are separate from image publication.
