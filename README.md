# Buzz Transcription for Unraid

The real [Buzz](https://github.com/chidiwilliams/buzz) desktop application, accessible in a browser, with NVIDIA GPU transcription and persistent storage. This is an unofficial container maintained by StormAvenger.

**Status:** [v0.1.0 is available](https://github.com/StormAvenger/buzz-unraid/releases/tag/v0.1.0). Tested on Unraid 7.3.4 with a GTX 1080 8 GB. A public speech sample uploaded through the browser was transcribed with Faster Whisper Small, producing TXT, SRT, and VTT files. This is one tested configuration, not a compatibility claim for every GPU or workflow. See [validation details](docs/VALIDATION.md).

Public image: `ghcr.io/stormavenger/buzz-unraid:latest` (stable updates), or `ghcr.io/stormavenger/buzz-unraid:0.1.0` (fixed version). No registry login is required. **Community Applications approved the submission on October 27, 2026. The listing should appear after the next catalog build publishes.**

## Set up Buzz on Unraid

The NVIDIA Driver plugin must already be installed and working. Once the catalog updates, search for **Buzz-Transcription** in Unraid's **Apps** tab. If the listing has not appeared yet, install the template with these commands in Unraid's Terminal:

```sh
mkdir -p /boot/config/plugins/dockerMan/templates-user
curl --fail --location --output /boot/config/plugins/dockerMan/templates-user/my-Buzz-Transcription.xml \
  https://raw.githubusercontent.com/StormAvenger/buzz-unraid/main/templates/buzz.xml
```

Go to **Docker → Add Container**, select **Buzz-Transcription** from the templates, and choose just two folders:

1. **Input folder:** where your audio and video files are stored.
2. **Output folder:** where you want transcripts and subtitles saved.

Click **Apply**, then click the Buzz icon and choose **WebUI**. All other settings are prefilled under **Show more settings**, including appdata, browser uploads, GPU selection, and web port **8088**. Change those only if your setup needs it.

## Use Buzz

1. Start the container and choose **WebUI** from its Unraid icon menu.
2. For existing server recordings, import files from `/input` using Buzz's **+** button.
3. For laptop files, click **Upload files** in the top bar and choose your recordings. Upload progress appears automatically. Use Buzz's **+** button to import the uploaded files from `/uploads`.
4. Start with **Faster Whisper → Small**. These are first-run defaults; later choices are preserved.
5. Click **Download transcripts** in the top bar to browse finished TXT, SRT, and VTT files and save them to your computer. Exports also appear in your chosen output folder on Unraid.

The first use downloads the chosen model into appdata. Subsequent local transcription can run without a cloud API. Telemetry is disabled. URL downloads and optional API features need their respective network services.

If the desktop looks small, open the browser sidebar → **Settings → Scaling Mode → Remote Resizing**. This fits the desktop to the browser window and is saved in that browser.

This is a single-user desktop session: browser connections share one Buzz application and history. Use it on a trusted LAN or through a VPN. Browser audio playback is configured but has not been verified; microphone forwarding is not configured.

## Storage

| Container folder | Default Unraid folder | Access | Purpose |
|---|---|---|---|
| `/config` | `/mnt/user/appdata/buzz-transcription` | Read/write | Settings, history, model downloads and caches |
| `/input` | `/mnt/user/transcription-input` | Read-only | Existing recordings |
| `/uploads` | `/mnt/user/transcription-uploads` | Read/write | Browser uploads |
| `/output` | `/mnt/user/transcriptions` | Read/write | Transcripts and subtitles |

The browser file manager is limited to the three media folders. Buzz can see the container filesystem and the folders explicitly mapped into it. The default user/group IDs are Unraid's `99:100` (`nobody:users`). Existing writable folders must permit those IDs to write. Startup initializes only the top level of a newly empty uploads/output folder; it does not recursively change existing media shares. The dedicated appdata tree is managed by the GUI base.

Automatic exports use `/output` unless a task explicitly chooses another destination. In manual Save/Export dialogs, select `/output`. Buzz's watched-folder mode moves or deletes sources, so it is not configured for read-only `/input`.

Existing installations retain their saved name and appdata mapping. New installs use the distinct name and `/mnt/user/appdata/buzz-transcription` folder to avoid overlap with the unrelated Buzz collaboration app. Before installing both apps on the same server, rename any existing transcription container to `Buzz-Transcription` and give each app its own non-overlapping appdata folder.

## Build and install locally on Unraid

For development or a custom build, use the Unraid server or another Linux amd64 Docker host. Normal installations can use the published image above.

1. Clone or extract this repository into a dedicated build directory, such as `/mnt/user/appdata/buzz-build/buzz-unraid`. Keep it separate from `/mnt/user/appdata/buzz-transcription`, which stores application data.
2. Choose an input folder for recordings and an output folder for transcripts. The remaining folder settings are prefilled.
3. Build:

   ```sh
   cd /mnt/user/appdata/buzz-build/buzz-unraid
   docker build --platform linux/amd64 -t buzz-unraid:0.1.0-dev .
   ```

   The ML dependency stack is substantial. Allow generous Docker storage and time for the first build. The final image build checks that the actual runtime can create Buzz's window, import its decoders, preserve preferences, and route exports correctly.

4. Generate the development template using the image's Python interpreter, even if Unraid does not have Python installed:

   ```sh
   docker run --rm --entrypoint /opt/venv/bin/python \
     -v "$PWD:/source:ro" buzz-unraid:0.1.0-dev \
     /source/scripts/local-template.py \
     > /boot/config/plugins/dockerMan/templates-user/my-Buzz-Transcription.xml
   ```

5. Go to **Docker → Add Container → Buzz-Transcription**, choose your **Input folder** and **Output folder**, and click **Apply**. The template uses the locally built image; it is not a Docker Hub image.
6. Click the Buzz icon and choose **WebUI**. The default web port is **8088**. If another app uses it, expand **Show more settings** and change **Web port**.

The NVIDIA Driver plugin/runtime must already work on Unraid. Host drivers stay on the server; the image supplies user-space CUDA libraries. For one NVIDIA GPU, `NVIDIA_VISIBLE_DEVICES=all` is sufficient. With multiple cards, use the intended GPU UUID from `nvidia-smi -L`.

Unraid's **Autostart** is a separate setting in its Docker page. Enable it there if you want Buzz to start after a server reboot.

## Updates

Use `ghcr.io/stormavenger/buzz-unraid:latest` to receive stable releases through Unraid's Docker update checks. For automatic installation, enable your Buzz-Transcription container in the **Auto Update Applications** plugin and choose a schedule. GitHub builds, checks, and publishes the image when a stable release is published; Unraid downloads that image from GHCR.

Back up appdata before upgrading. Keep the previous version tag and its matching backup for rollback. Selecting a fixed tag such as `:0.1.0` keeps that version until you change it.

## GPU verification

In the container's Console:

```sh
python /opt/buzz/gpu-check.py
```

This runs real CUDA computation and queries CTranslate2's supported compute types. Card detection alone is not sufficient. To test CUDA inference with a clearly spoken recording:

```sh
python /opt/buzz/gpu-check.py --transcribe /input/sample.wav
```

This downloads Tiny if needed and transcribes using `int8_float32`. Also test through the Buzz UI to exercise its complete workflow.

The image pins PyTorch 2.8.0 CUDA 12.6 because newer CUDA builds can omit Pascal support. It adapts Faster Whisper's reduced-memory mode to `int8_float32` when the GPU lacks `int8_float16` support. Larger models, other GPUs, speaker identification, and speech separation need separate testing.

## Compose alternative

```sh
cp .env.example .env
# Edit the folder paths and GPU selection in .env.
docker compose -f compose.yaml -f compose.nvidia.yaml up -d --build
```

For a browser/CPU test without requesting a GPU, omit the NVIDIA override:

```sh
docker compose up -d --build
```

Both target Linux amd64; this is not a native Apple Silicon image.

## Development and releases

```sh
python3 -m unittest discover -s tests -v
docker compose -f compose.yaml -f compose.nvidia.yaml config --quiet
docker build --platform linux/amd64 -t buzz-unraid:0.1.0-dev .
sh scripts/smoke-test.sh buzz-unraid:0.1.0-dev
```

The disposable CPU smoke test checks web readiness, the real application window, write permissions, and restart persistence. It removes only its own test container and anonymous volumes. The normal GitHub workflow builds/tests; it does not publish images. The separate **Publish image** workflow runs on published GitHub releases after the redistribution/source review described in [publishing notes](docs/PUBLISHING.md).

Runtime plugin package installation is blocked by default to keep dependencies predictable. Disabled plugins do not attempt dependency installation. Plugins requiring extra packages need those packages added to the image and a rebuild. The explicit runtime-install override forfeits the locked-dependency guarantee and is not supported for the standard deployment.

For upgrades, stop the container, back up appdata, and retain the previous image before changing versions. Database changes may require the matching appdata backup for rollback. See [maintenance decisions](docs/MAINTENANCE.md) for dependency pins and the TorchCodec compatibility override.

## License

Container-specific code and original assets are licensed under the [MIT License](LICENSE).

Buzz is also MIT licensed. Bundled third-party software retains its respective licenses; see [third-party notices](THIRD_PARTY_NOTICES.md).
