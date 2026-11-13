# Buzz Transcription for Unraid

The real [Buzz](https://github.com/chidiwilliams/buzz) desktop in your browser, with NVIDIA transcription and persistent storage; an unofficial container maintained by StormAvenger.

[![Latest release](https://img.shields.io/github/v/release/StormAvenger/buzz-unraid)](https://github.com/StormAvenger/buzz-unraid/releases/latest)
[![License](https://img.shields.io/github/license/StormAvenger/buzz-unraid)](LICENSE)

## Features

- Real Buzz desktop, accessible in a browser.
- NVIDIA GPU acceleration for transcription.
- Upload files and download transcripts from the toolbar.
- Persistent settings, models, and history.
- Startup and GPU status with private diagnostics.

## Requirements & supported hardware

Use an **amd64 Unraid server** with the **NVIDIA Driver plugin** installed and working.

- **Tested:** GTX 1080 (Pascal).
- **Expected to work, untested:** other NVIDIA GTX 10 through RTX 40 cards.
- **Not supported yet:** RTX 50 (Blackwell), AMD, Intel, or Apple Silicon.
- CPU-only transcription works but is slow; the supplied Unraid template requires the NVIDIA runtime.

Uses a CUDA 12.6 PyTorch build, the last line that supports Pascal GPUs.

## Install

Open **Apps → search Buzz-Transcription → Install**. Choose your **Input folder** and **Output folder**, click **Apply**, then choose **WebUI** from the container’s icon menu.

Everything else is prefilled under **Show more settings**.

## Using Buzz

1. Click **Upload files** in the top bar and choose recordings from your computer.
2. Click Buzz’s **+** button. The picker defaults to `/uploads`; after selecting another folder, Buzz remembers it. Open `/input` for existing server recordings.
3. Start with **Faster Whisper → Small**, choose transcription options, and start processing.
4. Click **Download transcripts** to save finished TXT, SRT, or VTT files. Exports also appear in your Output folder.
5. Use **Back to main page** to leave live recording without stopping file jobs.

## Folders

| Container folder | Default Unraid folder | Access | Purpose |
|---|---|---|---|
| `/config` | `/mnt/user/appdata/buzz-transcription` | Read/write | Settings, history, models and caches |
| `/input` | `/mnt/user/transcription-input` | Read-only | Existing recordings |
| `/uploads` | `/mnt/user/transcription-uploads` | Read/write | Browser uploads |
| `/output` | `/mnt/user/transcriptions` | Read/write | Transcripts and subtitles |

Writable folders must allow Unraid’s default user/group **99:100** (`nobody:users`) to write.

## Updates & backups

Use `ghcr.io/stormavenger/buzz-unraid:latest` for stable updates, or a version tag from the [Releases page](https://github.com/StormAvenger/buzz-unraid/releases) to stay on a particular release. Check for updates on Unraid’s Docker page; for automatic installation, select Buzz in the **Auto Update Applications** plugin and choose a schedule.

Back up appdata before upgrading. Keep the previous image tag and its matching backup for rollback. Dependency updates are larger downloads than app-only updates, which reuse the dependency layers.

## Troubleshooting

- **GPU unavailable:** check the NVIDIA Driver plugin and GPU selection under **Show more settings**. In the container’s Console, run:

  ```sh
  python /opt/buzz/gpu-check.py
  python /opt/buzz/gpu-check.py --transcribe /input/sample.wav
  ```

  Replace `sample.wav` with a spoken recording in your Input folder; the second check downloads Tiny if needed.
- **Desktop looks small:** browser sidebar → **Settings → Scaling Mode → Remote Resizing**.
- **Permission errors:** check writable-folder ownership and permissions for **99:100**.
- **Port 8088 in use:** change **Web port** under **Show more settings**.
- **Manual template fallback:** run in Unraid’s Terminal, then use **Docker → Add Container → Buzz-Transcription**:

  ```sh
  mkdir -p /boot/config/plugins/dockerMan/templates-user
  curl --fail --location -o /boot/config/plugins/dockerMan/templates-user/my-Buzz-Transcription.xml \
    https://raw.githubusercontent.com/StormAvenger/buzz-unraid/main/templates/buzz.xml
  ```

For more information about a problem, download **Diagnostics** from the top bar.

## Security & privacy

This is a single-user session: browser connections share the desktop and history. Use a trusted LAN or VPN; no login is available yet. Telemetry is disabled, and diagnostics stay local until you choose to share them. The first model download comes from Hugging Face; later local transcription can run offline. URL imports and optional API features need their respective services.

## Limitations

No microphone forwarding. Browser audio playback is unverified. Buzz plugins needing extra Python packages are unsupported. Faster Whisper is the tested backend.

## Support

Report problems through [GitHub Issues](https://github.com/StormAvenger/buzz-unraid/issues) and attach the **Diagnostics JSON**.

Building from source: [development guide](docs/DEVELOPMENT.md).

## License

Container-specific code and original assets are licensed under the [MIT License](LICENSE).

Buzz is also MIT licensed. Bundled third-party software retains its respective licenses; see [third-party notices](THIRD_PARTY_NOTICES.md).
