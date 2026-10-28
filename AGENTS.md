# Working on Buzz for Unraid

Read this file first. Keep changes small enough to review as a diff.

## Repository map

- `Dockerfile`: app layers and runtime checks; `Dockerfile.deps`: pinned cu126 OS/Python environment.
- `scripts/dependency.py`, `docs/DEPENDENCIES.md`: input identity, approved digest/source resolution, bootstrap and layer evidence.
- `requirements/`: exact Python inputs, hash locks, corresponding-source pins.
- `rootfs/`: app startup/storage, readiness/GPU checks, noVNC toolbar.
- `scripts/patch-buzz.py`, `scripts/patch-web-ui.py`: guarded upstream changes.
- `scripts/smoke-test.sh`: disposable browser, permissions, storage and restart checks.
- `scripts/release-inventory.py`, `scripts/collect-sources.py`: clean-image notices and matching sources.
- `.github/workflows/`: container CI and publication gates.
- `templates/buzz.xml`: the single public Unraid template; `ca_profile.xml`: repository profile.
- `docs/MAINTENANCE.md`: architecture and compatibility decisions.
- `docs/VALIDATION.md`: current verification procedure and limits. Put release-specific results in GitHub release notes.
- `docs/ROADMAP.md`: deferred features. Private working notes end in `.local.md` and must remain ignored.

## Invariants

- Never publish private recordings, transcripts, appdata, models, credentials, local notes, personal host/IP/path information, or raw diagnostic logs. Collect inventories only from clean images with no user mounts.
- Preserve telemetry-off defaults and the diagnostic allowlists. Never export environment or application/database dumps.
- Keep exact base/tool/action pins and artifact hashes. Upstream patch drift must fail the build before any partial writes.
- No runtime package installation. Preserve the cuDNN-header and W&B executable exclusions before dependency files enter a distributable layer.
- Preserve MIT and third-party notices and matching-source availability for every published binary.
- Do not change ports, volume mappings, template defaults, CUDA/PyTorch versions, or application behavior as a side effect of maintenance.
- Do not touch a user's running container or data for testing. Use named disposable containers and anonymous volumes; remove those test containers/volumes afterwards.

## Branch and review workflow

Never use [skip ci] on PR branches; required checks must run.

1. Check `git status`; preserve unrelated work. Create a `codex/` branch from the intended base before editing.
2. Make one phase per PR. Run applicable checks and describe the concrete problem, behavior, validation and limitations in its body.
3. Open and attach the PR, give the user its number and review range, and leave it unmerged. Stacked PRs must name their prerequisite and target that branch until it merges.
4. Do not push to `main`, bypass branch protection, or merge unless the human explicitly requests it. Required container CI must pass before merging.

## Update a dependency

1. Read `docs/MAINTENANCE.md`; identify compatibility/source obligations and limit the PR to the requested update.
2. Update the appropriate input/pin and regenerate locks with the pinned uv version using `scripts/lock-dependencies.sh`. Review the entire lock diff and any resolver overrides.
3. Update matching-source pins and notices where required. Preserve Pascal/cu126 support unless the requested change explicitly says otherwise.
4. Run public-file checks, Python/JavaScript tests, Compose and build-context validation, full Linux build, runtime and disposable smoke checks. Check patch application against the actual pinned upstream files.
5. Run the image scan gate and source collection. Never suppress findings or waive missing sources to obtain a green release.
6. Record GPU checks on relevant hardware separately from CPU CI. Open a PR with the changed versions, tests and remaining limits.

## Cut a release

1. Obtain the human's publication instruction. Use a reviewed commit with passing required CI and a clean public source tree.
2. Verify the GitHub `release` environment has the owner configured as a required reviewer. An environment name alone provides no approval protection. Never remove reviewers or approve on the human's behalf.
3. Create a new immutable version tag at the tested commit; never move an existing release tag. Publish clear notes with known limits and mark image publication pending until its workflow succeeds.
4. Let the environment approval and all build/runtime/privacy/scan/source gates pass. Never bypass a gate or publish from private appdata.
5. Verify public anonymous image access, version/revision labels, checksums and source links, matching stable/versioned digests, and appropriate disposable hardware/browser checks. Keep older releases and sources available.
6. Update release notes with evidence and digest, then current documentation through a separate reviewed PR. Report what was published and leave installation to the user unless they explicitly requested deployment.
