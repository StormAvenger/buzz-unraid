# Publishing and Community Applications

## Current state

The source is public at [StormAvenger/buzz-unraid](https://github.com/StormAvenger/buzz-unraid) under MIT. [v0.1.2](https://github.com/StormAvenger/buzz-unraid/releases/tag/v0.1.2) publishes the image as `ghcr.io/stormavenger/buzz-unraid:0.1.2` and `:latest`, with inventory, notices, scan results, matching sources, and checksums attached to the release. The [publication workflow](https://github.com/StormAvenger/buzz-unraid/actions/runs/40699900685) passed all gates.

The official Community Applications scan found one valid Docker app, no hard errors, no template warnings, no starter placeholders, and a publicly pullable image. The submission was sent and auto-approved on October 27, 2026 as a non-duplicated Docker app. The portal says the app should appear after the next Community Applications catalog build publishes; catalog visibility has not yet been verified.

The template now uses **Buzz-Transcription** with dedicated default appdata at `/mnt/user/appdata/buzz-transcription`, avoiding the unrelated Buzz collaboration app. The image tags and template URL are unchanged; existing installations retain their saved data mappings.

## 1. Publish the source repository

Keep the repository public. Include the Dockerfile, complete container-specific source/patches, dependency inputs and locks, tests, MIT license, original Buzz MIT notice, and third-party notices. Do not publish appdata, downloaded models, recordings, credentials, build logs, or machine-specific deployment notes.

GitHub's **Check container** workflow builds/tests the project on Linux amd64. The first complete hosted build and CPU smoke test passed on October 26, 2026. Keep these checks passing before cutting a release; future dependency updates may change this large ML stack's storage requirements.

## 2. Prepare and publish a downloadable image

For every binary release, collect the actual dependency/license inventory, preserve required notices, and provide matching source downloads for redistributed components (including PyQt/Qt, FFmpeg, and GPL/LGPL components). A link to an arbitrary upstream main branch is not a substitute for the corresponding versions. Review NVIDIA runtime redistribution terms when updating those components. See [REDISTRIBUTION.md](REDISTRIBUTION.md) for the v0.1.0 component review and exclusions.

The **Publish image** workflow runs when a GitHub release is published. Create a release tagged `v0.1.0` (or a later version) from the reviewed commit. The workflow builds/tests the image, collects the installed package inventory and notices from a clean image, scans it, downloads matching upstream sources, and attaches the records and checksums to that release before pushing the image. A stable release updates `ghcr.io/stormavenger/buzz-unraid:latest`; prerelease tags and releases marked as prereleases do not change `:latest`.

For preparation without publishing, run the workflow manually with **publish** unchecked. Inspect its `release-records` artifact. Preparation artifacts retain metadata and notices for seven days; full source archive parts are attached directly to the matching GitHub release during publication, avoiding a duplicate multi-gigabyte Actions artifact. A manual publish requires an existing matching `vVERSION` GitHub release. Source collection fails the workflow if required source records or downloads are missing. Review the scan and the source manifest before the first public image.

The source archive list is tied to the pinned Qt, PyAV, Torch and GUI base versions. Update `requirements/cu126/source-archives.json` when those dependencies change. `inventory.json` records the actual installed versions. `source-manifest.json` records archive origins and SHA-256 hashes. The source download parts can be joined and extracted with `cat sources.tar.part* | tar -xf -`; `notices.tar.gz` retains installed and collected upstream notices. Keep these assets available for as long as the corresponding image is offered.

The workflow uses the repository's temporary `GITHUB_TOKEN`; it does not require a personal access token. After the first publish, check the package's visibility: GHCR packages are initially private by default. For a public Unraid listing, the image must be public and pullable without credentials. Test an anonymous pull and clean installation on another Docker/Unraid host. Include version/digest, dependency inventory, image scan results, source download links, test results, and known limitations in the release notes.

Sources: [GHCR authentication and visibility](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).

## 3. Finalize the Unraid listing

The repository includes one public Docker app XML at `templates/buzz.xml`, the root `ca_profile.xml`, an MIT root license, original `icon.svg`, and GitHub issue support. The template includes the public image, WebUI, read-only source mapping, writable output/upload mappings, NVIDIA settings, and raw TemplateURL.

A dedicated Unraid forum support thread is useful for users; add its real URL if one is created. Never invent a thread URL. GitHub Issues is the support destination.

## 4. Submit through Community Applications

Use the current [Community Applications submission portal](https://ca.unraid.net/submit), not an assumed older forum-message workflow:

1. Sign in and enter the public repository URL.
2. Run **Validate**, then **Scan**; resolve XML/profile, image, duplicate, and listing issues.
3. Review the generated listing preview, including the GPU requirement and tested hardware.
4. Complete the submission and its applicable terms as the repository owner.
5. Wait for moderator approval. Approved entries appear after a catalog build; do not promise a publication deadline.

The portal requires an active public repository, an OSI-approved root LICENSE, a root `ca_profile.xml` with a non-empty Profile, and valid app XML. A GitHub repository existing does not mean the app has been submitted or accepted.

Sources: [official submission help](https://ca.unraid.net/submit/help), [repository XML](https://ca.unraid.net/submit/help/repository-xml), [profile XML](https://ca.unraid.net/submit/help/repository-info-xml), [official starter](https://github.com/unraid/unraid-community-apps-starter).

## 5. Maintain the release

Publish immutable version tags and update `:latest` only after tests. Keep older images and their corresponding sources available for rollback and redistribution obligations. Review GPU architecture support before upgrading CUDA/PyTorch/CTranslate2. Repeat clean installation and recreation testing for meaningful changes. Update the template when mappings, required variables, ports, or GPU prerequisites change, and respond to support issues.

## Split-image releases

For the cu126 split workflow, matching upstream source bundles live on the exact dependency release linked by the app release’s `SOURCE-README.txt` and `dependency-image.json`. Each app release still supplies its fresh inventory, notices, scan and checksums, plus the app patches/recipes in its source archive. Keep both releases available. See [DEPENDENCIES.md](DEPENDENCIES.md) for approval, bootstrap and layer verification procedures. Historical releases retain their original bundled sources.
