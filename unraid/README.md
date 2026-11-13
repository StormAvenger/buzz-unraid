# Unraid templates

The single Community Applications template is [../templates/buzz.xml](../templates/buzz.xml). It uses the public `ghcr.io/stormavenger/buzz-unraid:latest` image. Install **Buzz-Transcription** from Unraid’s **Apps** tab; see the [installation guide](../README.md#install).

To install the locally built `buzz-unraid:dev` image, generate a local template rather than publishing a second app entry:

```sh
python3 scripts/local-template.py > /boot/config/plugins/dockerMan/templates-user/my-Buzz-Transcription.xml
```

If Python is unavailable on Unraid, use the generator container command in the [development guide](../docs/DEVELOPMENT.md#build-and-install-locally-on-unraid). Existing installed Unraid templates are unaffected by this repository layout.

The public app name is **Buzz-Transcription** and its default appdata folder is `/mnt/user/appdata/buzz-transcription`. The template URL stays the same so the approved repository can update its existing template. Existing installs retain their saved names and folder mappings.
