# Publishing and Community Applications

## Current state

The source is prepared for `StormAvenger/buzz-unraid` under GPL-3.0-only, matching creator5-ha. The development container has passed the server checks in [VALIDATION.md](VALIDATION.md). The public image and Unraid listing are separate releases and are not yet available.

## 1. Publish the source repository

Keep the repository public. Include the Dockerfile, complete container-specific source/patches, dependency inputs and locks, tests, GPL license, original Buzz MIT notice, and third-party notices. Do not publish appdata, downloaded models, recordings, credentials, build logs, or machine-specific deployment notes.

GitHub's **Check container** workflow builds/tests the project on Linux amd64. Fix any CI failures before cutting a release. The hosted runner's disk requirements must be verified with this large ML stack; the image has only been built on the Unraid host so far.

## 2. Prepare and publish a downloadable image

Before the first public binary image, complete the actual dependency/license inventory, preserve required notices, and arrange the corresponding-source downloads required by redistributed components (including PyQt/Qt, FFmpeg, and any GPL/LGPL components). A link to an arbitrary upstream main branch is not a substitute for the corresponding versions. Review NVIDIA runtime redistribution terms as well. This review is still pending; source publication alone does not complete it.

The **Publish image** workflow is manual. After the above work, run it from the main branch with a version such as `0.1.0`. It builds the image, runs the disposable smoke test, and pushes the versioned image to `ghcr.io/stormavenger/buzz-unraid:0.1.0`. A non-prerelease version also updates `:latest`; prerelease tags do not change `:latest`.

The workflow uses the repository's temporary `GITHUB_TOKEN`; it does not require a personal access token. After the first publish, check the package's visibility: GHCR packages are initially private by default. For a public Unraid listing, the image must be public and pullable without credentials. Test an anonymous pull and clean installation on another Docker/Unraid host. Include version/digest, dependency inventory, image scan results, source download links, test results, and known limitations in the release notes.

Sources: [GHCR authentication and visibility](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).

## 3. Finalize the Unraid listing

The repository includes one public Docker app XML at `templates/buzz.xml`, the root `ca_profile.xml`, a GPL root license, original `icon.svg`, and GitHub issue support. The template already has the planned public image, WebUI, read-only source mapping, writable output/upload mappings, NVIDIA settings, and raw TemplateURL. Do not submit while the image is unavailable.

A dedicated Unraid forum support thread is useful for users; add its real URL if one is created. Never invent a thread URL. GitHub Issues is the current planned support destination.

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
