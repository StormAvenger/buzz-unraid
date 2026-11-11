# Building and developing Buzz for Unraid

Normal installations use Community Apps; see the [user guide](../README.md#install). Development builds target Linux amd64. Native Apple Silicon builds are unsupported.

## Build and install locally on Unraid

Use Unraid or another Linux amd64 Docker host. Clone or extract the repository into a dedicated build directory, separate from production appdata. From the repository root:

```sh
docker build -f Dockerfile.deps -t buzz-unraid-deps:local .
docker build --build-arg DEPS_IMAGE=buzz-unraid-deps:local -t buzz-unraid:dev .
```

These commands require Docker, not host Python. Allow generous Docker storage and time for the first dependency build. The app build checks that the shipped runtime creates Buzz’s window, imports its decoders, preserves preferences, and routes exports correctly.

Generate the local Unraid template with the image’s Python interpreter:

```sh
mkdir -p /boot/config/plugins/dockerMan/templates-user
docker run --rm --entrypoint /opt/venv/bin/python \
  -v "$PWD:/source:ro" buzz-unraid:dev \
  /source/scripts/local-template.py \
  > /boot/config/plugins/dockerMan/templates-user/my-Buzz-Transcription.xml
```

Under **Docker → Add Container → Buzz-Transcription**, choose separate test Input, Output and appdata folders, then **Apply → WebUI**. The default web port is **8088**; change it under **Show more settings** if occupied. Avoid replacing a production installation with a development template.

The NVIDIA Driver plugin/runtime must already work on Unraid. Host drivers stay on the server; the image supplies user-space CUDA libraries. For one GPU, `NVIDIA_VISIBLE_DEVICES=all` is sufficient; with multiple cards, select the intended GPU UUID from `nvidia-smi -L`. Unraid’s **Autostart** setting is separate, on its Docker page.

## Compose alternative

For CI/development hosts with Python, the helper handles dependency identity and approved digests:

```sh
cp .env.example .env
# Edit .env: use separate test folders, a free web port and your GPU selection.
python3 scripts/dependency.py build --bootstrap --image buzz-unraid:dev
```

Start the NVIDIA configuration using the locally built `buzz-unraid:dev` image:

```sh
docker compose -f compose.yaml -f compose.nvidia.yaml up -d --no-build
```

For a browser/CPU test without requesting a GPU:

```sh
docker compose up -d --no-build
```

Both paths target Linux amd64.

## Development and releases

Read [AGENTS.md](../AGENTS.md) before changes. Keep one phase per review PR, run CI without skipping checks, and leave merging and publication approval to the human reviewer.

```sh
python3 scripts/check-public-files.py
python3 -m unittest discover -s tests -v
node --test tests/test_status.mjs
docker compose -f compose.yaml -f compose.nvidia.yaml config --quiet
sh scripts/check-build-context.sh
python3 scripts/dependency.py build --bootstrap --image buzz-unraid:dev
sh scripts/smoke-test.sh buzz-unraid:dev
```

The disposable CPU smoke test checks web readiness, the real application window, write permissions, and restart persistence. It removes only its own test container and anonymous volumes. Record GPU hardware checks separately; a CPU build does not establish GPU compatibility.

Runtime plugin package installation is blocked by default to keep dependencies predictable. Disabled plugins do not attempt dependency installation. Plugins requiring extra packages need those packages included in a reviewed image rebuild. The unsupported runtime-install override forfeits the locked-dependency guarantee.

The normal **Check container** workflow builds and tests without publishing. The separate **Publish image** workflow runs on published GitHub releases, behind release approval and build, privacy, scan and source gates. Never waive scan findings or missing sources to publish.

Further procedures:

- [Validation and hardware/browser checks](VALIDATION.md)
- [Dependency identity, builds and layer evidence](DEPENDENCIES.md)
- [Publication and Community Apps](PUBLISHING.md)
- [Maintenance decisions and compatibility overrides](MAINTENANCE.md)
- [Redistribution and matching sources](REDISTRIBUTION.md)

For update and rollback advice, see [Updates & backups](../README.md#updates--backups).
