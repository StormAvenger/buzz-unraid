# Image contents and release records

The repository's original code and assets use MIT. Bundled components retain their own licenses, including the Qt/PyQt and FFmpeg licenses and NVIDIA runtime terms. The image's installed notices and matching release assets identify those components and versions.

## Sources and notices

Each published image has a matching GitHub release containing:

- `inventory.json`: installed Python and Ubuntu package versions, plus the actual PyAV FFmpeg configuration.
- `notices.tar.gz`: installed copyright/license files and notices collected from upstream source archives.
- `source-manifest.json`: source locations, exact versions, checksums, and packages with separate source handling.
- `sources.tar.partNNN`: matching sources, upstream build recipes, and Ubuntu source packages/patches.
- `image-scan.json` and `SHA256SUMS`: vulnerability findings and release-file integrity checks.

Download all source parts and join/extract them with `cat sources.tar.part* | tar -xf -`. The repository's Dockerfile, locked dependencies, and patches accompany these upstream sources. Application data, recordings, downloaded models, and host configuration are excluded from collection.

The PyAV lamer source is pinned to commit `3ffd14f5531e0e5078e31eba4b2fb6ccc277b843`, the v3.101.0 release used by its vendor build recipe. The upstream repository was renamed from lamer to bwlame, changing GitHub's generated archive and checksum; the collector uses the canonical repository and exact release commit. The lameenc 1.9.0 wrapper and its pinned LAME source are collected separately.

## NVIDIA components

The image uses CUDA 12.6 runtime packages and cuDNN 9.10.2 supplied as PyTorch dependencies. The host supplies its own NVIDIA driver. NVIDIA copyright and license files stay in the installed distributions and the release notice archive. NCCL and NVTX retain their separately supplied license terms.

CUDA's distribution grant and Attachment A identify runtime components that can accompany an application with additional functionality. The image provides transcription functionality; NVIDIA components retain their terms and are used for NVIDIA GPU inference. See the [CUDA 12.6 EULA and Attachment A](https://docs.nvidia.com/cuda/archive/12.6.3/eula/index.html).

The [cuDNN 9.10.2 supplement](https://docs.nvidia.com/deeplearning/cudnn/backend/v9.10.2/reference/eula.html) identifies runtime `.so`/`.dll` files for redistribution. Its development headers are removed in the builder before copying the environment into the runtime stage, so they never enter a published image layer. The runtime libraries and license files are retained. The [cuSPARSELt supplement](https://docs.nvidia.com/cuda/cusparselt/license.html) separately permits its runtime `.so` and `.h` files.

These records describe the release packaging and component terms. Model weights downloaded later have their own licenses. Redistributors must preserve the notices and source availability for the versions they offer, and review changed vendor terms when updating dependencies.
