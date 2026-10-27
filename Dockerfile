# syntax=docker/dockerfile:1
# SPDX-License-Identifier: MIT
ARG GUI_IMAGE=jlesage/baseimage-gui:ubuntu-24.04-v4.14.0@sha256:8004b5799addeb62e5ce2fed3b611016433faeb4f9d2126956128699b45fa3ee
FROM ghcr.io/astral-sh/uv:0.13.5@sha256:32a7bb39b496babbd997b0a39a4d66c126bdaf5661b302bf6f06abda8deca6ff AS uv
FROM ${GUI_IMAGE} AS common
# The base creates account files at startup; avoid build-time name/group lookup.
USER 0:0
RUN add-pkg \
    ca-certificates ffmpeg fonts-dejavu-core gettext libasound2t64 \
    libegl1 libgl1 libglib2.0-0t64 libgomp1 libportaudio2 libpulse0 \
    libsndfile1 libtbb12 libvulkan1 libxkbcommon-x11-0 libxcb-cursor0 \
    libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
    libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 \
    python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*

FROM common AS builder
COPY --from=uv /uv /usr/local/bin/uv
RUN add-pkg \
    build-essential python3-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*
ENV UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
RUN uv venv --python /usr/bin/python3 /opt/venv
COPY requirements/ /build/requirements/
# diffq's legacy build needs NumPy and Cython in its build environment.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --python /opt/venv/bin/python --require-hashes \
        -r /build/requirements/build.lock \
    && uv pip install --python /opt/venv/bin/python --require-hashes --no-deps \
        --no-build-isolation-package diffq -r /build/requirements/runtime.lock
COPY scripts/patch-buzz.py /build/patch-buzz.py
RUN /opt/venv/bin/python /build/patch-buzz.py /opt/venv/lib/python3.12/site-packages
FROM common AS runtime
ARG IMAGE_VERSION=0.1.0-dev
ARG SOURCE_REVISION=unknown
LABEL org.opencontainers.image.title="Buzz for Unraid" \
    org.opencontainers.image.source="https://github.com/StormAvenger/buzz-unraid" \
    org.opencontainers.image.revision="${SOURCE_REVISION}" \
    org.opencontainers.image.version="${IMAGE_VERSION}" \
    org.opencontainers.image.description="Unofficial Buzz browser desktop container with NVIDIA transcription"
# TorchCodec links to the shared Python library; python3 alone does not ship it.
RUN add-pkg libpython3.12t64 && rm -rf /var/lib/apt/lists/*
COPY --from=builder /opt/venv /opt/venv
COPY rootfs/ /
COPY scripts/patch-web-ui.py /opt/buzz/patch-web-ui.py
RUN /opt/venv/bin/python /opt/buzz/patch-web-ui.py
COPY requirements/*.lock /usr/share/buzz-container/
COPY LICENSE THIRD_PARTY_NOTICES.md /usr/share/buzz-container/
COPY licenses/ /usr/share/buzz-container/licenses/
RUN chmod +x /startapp.sh /etc/cont-init.d/55-buzz-storage.sh \
    && mkdir -p /input /uploads /output \
    && set-cont-env APP_NAME "Buzz" \
    && set-cont-env APP_VERSION "1.4.5" \
    && set-cont-env DOCKER_IMAGE_VERSION "${IMAGE_VERSION}" \
    && printf '%s\n' \
        "Sources, notices and package records for this image:" \
        "https://github.com/StormAvenger/buzz-unraid/releases/tag/v${IMAGE_VERSION}" \
        "Download SOURCE-README.txt for source archive instructions." \
        > /usr/share/buzz-container/SOURCE-LOCATION.txt
# Verify the shipped runtime, without any build-only libraries available.
RUN QT_QPA_PLATFORM=offscreen BUZZ_DISABLE_TELEMETRY=1 \
    HF_HUB_DISABLE_TELEMETRY=1 /opt/venv/bin/python /opt/buzz/check-install.py
ENV PATH="/opt/venv/bin:${PATH}" \
    USER_ID=99 GROUP_ID=100 UMASK=0002 \
    KEEP_APP_RUNNING=1 WEB_AUDIO=1 WEB_FILE_MANAGER=1 \
    WEB_FILE_MANAGER_ALLOWED_PATHS=/input,/uploads,/output \
    WEB_TERMINAL=0 VNC_LOCALHOST_ONLY=1 \
    BUZZ_MODEL_ROOT=/config/cache/buzz/models \
    HF_HOME=/config/cache/huggingface TORCH_HOME=/config/cache/torch \
    XDG_STATE_HOME=/config/xdg/state \
    BUZZ_OUTPUT_DIRECTORY=/output \
    BUZZ_DISABLE_TELEMETRY=1 HF_HUB_DISABLE_TELEMETRY=1 \
    BUZZ_FORCE_CPU=false BUZZ_REDUCE_GPU_MEMORY=true \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility \
    QT_X11_NO_MITSHM=1 QT_OPENGL=software PYTHONUNBUFFERED=1
EXPOSE 5800
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD ["/opt/venv/bin/python", "/opt/buzz/healthcheck.py"]
# The GUI base supplies the entrypoint and runs /startapp.sh as USER_ID:GROUP_ID.
