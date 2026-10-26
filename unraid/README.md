# Unraid templates

The single Community Applications template is [../templates/buzz.xml](../templates/buzz.xml). It targets the planned public GHCR image; do not submit it until that image exists and can be pulled without authentication.

To install a locally built development image, generate a local template rather than publishing a second app entry:

```sh
python3 scripts/local-template.py > /boot/config/plugins/dockerMan/templates-user/my-buzz.xml
```

If Python is unavailable on Unraid, use the generator container command in the main README. Existing installed Unraid templates are unaffected by this repository layout.
