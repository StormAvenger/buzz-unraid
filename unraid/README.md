# Unraid templates

The single Community Applications template is [../templates/buzz.xml](../templates/buzz.xml). It uses the public `ghcr.io/stormavenger/buzz-unraid:latest` image. The main README explains manual installation while the Apps listing awaits submission and approval.

To install a locally built development image, generate a local template rather than publishing a second app entry:

```sh
python3 scripts/local-template.py > /boot/config/plugins/dockerMan/templates-user/my-buzz.xml
```

If Python is unavailable on Unraid, use the generator container command in the main README. Existing installed Unraid templates are unaffected by this repository layout.
