# cu126 dependency images

The dependency image contains Ubuntu packages and the unpatched Python environment. The app image inherits its layers and changes only the guarded application patches, rootfs, toolbar, notices and version records. It never copies the full Python environment again. CUDA/PyTorch versions, ports, mounts and the public template are unchanged. cu126 is the only supported build in this phase.

## Identity and approval

`python3 scripts/dependency.py key` computes a full SHA-256 over named input bytes: `Dockerfile.deps` (including GUI/uv digests), everything under `requirements/cu126/`, licenses/notices, and the source-collection/inventory recipes. Input names and lengths delimit the hash. Changes to rootfs, toolbar or app patches do not affect it. Source recipes are included so changed source obligations cannot silently reuse an old publication.

The image tag is `ghcr.io/stormavenger/buzz-unraid-deps:cu126-<key>`. Its source release is `deps-cu126-<key>`, marked as a prerelease so it does not become the latest app release. That release's `dependency-image.json` records the actual pushed immutable `@sha256:` reference. The app publication resolves and checks this record, checksums, matching package inventory and source asset digests, then pulls the image by digest and verifies its key/variant labels. Missing or incomplete records stop publication. A mutable tag is never accepted as a production base.

The dependency workflow only runs on changes to these inputs on main, or manually. Both publication workflows use the `release` environment; the owner must configure themselves as required reviewer. Workflow names alone do not create that protection. There is no scheduled OS upgrade in this phase. Changing repository packages requires an explicitly reviewed dependency recipe/input change; exact installed versions and sources are recorded for each resulting image.

## First publication after review

1. Review and merge the guardrails PR, then the dependency split PR. Leave existing app releases/tags untouched.
2. Configure the release environment's required owner approval and main's required PR/check protection in GitHub settings.
3. Approve the first dependency workflow. It builds a clean dependency image and app, runs the runtime/browser/layer checks, scans both images, and collects matching sources. Sources are attached before the dependency image is pushed. It then attaches the exact digest record and updated checksums.
4. Make the new `buzz-unraid-deps` GHCR package public if GitHub initially creates it private. The final anonymous verification must pass. Rerunning a complete publication verifies/reuses it instead of overwriting its tag. Incomplete releases fail closed and require owner inspection/recovery; do not delete available sources or move a published image tag to recover.
5. Only then approve a new app release from the reviewed commit. It uses the approved dependency digest, scans the full app and compares installed package identities before linking the dependency sources. No production installation is part of these workflows.

## Local and PR builds

Run `python3 scripts/dependency.py build --bootstrap --image buzz-unraid:0.1.2-dev`. This reuses the approved image if present, or builds a local unpublished dependency image when its release does not exist. This fallback is explicit and is never used by the app publication workflow. Then run Compose with `up -d --no-build`. For raw Compose builds, supply `DEPS_IMAGE` explicitly; the local placeholder is not an approved publication reference.

PR CI builds without publishing, runs the existing CPU/browser/storage checks, scans both clean images, and verifies sources. New dependency inputs collect sources in CI; app-only changes reuse the approved source records. Inventories and evidence are retained for seven days; multi-GB source bundles are attached once on dependency publication, rather than copied to every app release.

`python3 scripts/dependency.py layer-proof` makes a second app build from tracked sources with only a harmless toolbar CSS comment changed. It checks both full layer lists against the exact dependency-layer prefix and fails if app overhead exceeds 64 MiB. `dependency-layer-proof` CI artifacts contain the layer IDs and uncompressed byte sizes. This demonstrates content reuse; actual registry transfer sizes depend on compression/cache. No user files or host paths appear in this evidence.

App release records retain a fresh inventory, notices and full image scan. `SOURCE-README.txt` links to the exact matching dependency release, while the app's GitHub source archive contains its patches/build recipes. Keep both app and dependency releases available for as long as their binaries are distributed.
