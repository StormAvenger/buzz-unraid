# syntax=docker/dockerfile:1
# SPDX-License-Identifier: MIT
# Publication supplies an approved dependency image pinned by digest.
ARG DEPS_IMAGE
FROM ${DEPS_IMAGE} AS runtime
ARG IMAGE_VERSION=0.1.2-dev
ARG SOURCE_REVISION=unknown
ARG DEPENDENCY_KEY
ARG DEPENDENCY_SOURCES
LABEL org.stormavenger.buzz.dependency-key="${DEPENDENCY_KEY}" \
    org.stormavenger.buzz.dependency-sources="${DEPENDENCY_SOURCES}" \
    org.opencontainers.image.title="Buzz for Unraid" \
    org.opencontainers.image.source="https://github.com/StormAvenger/buzz-unraid" \
    org.opencontainers.image.revision="${SOURCE_REVISION}" \
    org.opencontainers.image.version="${IMAGE_VERSION}" \
    org.opencontainers.image.description="Unofficial Buzz browser desktop container with NVIDIA transcription"
COPY scripts/patch-buzz.py /opt/buzz/patch-buzz.py
RUN PYTHONDONTWRITEBYTECODE=1 /opt/venv/bin/python /opt/buzz/patch-buzz.py /opt/venv/lib/python3.12/site-packages
COPY rootfs/ /
COPY scripts/patch-web-ui.py /opt/buzz/patch-web-ui.py
RUN /opt/venv/bin/python /opt/buzz/patch-web-ui.py
COPY requirements/cu126/*.lock /usr/share/buzz-container/
COPY LICENSE THIRD_PARTY_NOTICES.md /usr/share/buzz-container/
COPY licenses/ /usr/share/buzz-container/licenses/
RUN chmod +x /startapp.sh /etc/cont-init.d/55-buzz-storage.sh /etc/cont-init.d/56-buzz-status.sh \
    && printf '%s\n' "${IMAGE_VERSION}" > /usr/share/buzz-container/VERSION \
    && mkdir -p /input /uploads /output \
    && set-cont-env APP_NAME "Buzz" \
    && set-cont-env APP_VERSION "1.4.5" \
    && set-cont-env DOCKER_IMAGE_VERSION "${IMAGE_VERSION}" \
    && printf '%s\n' \
        "Sources, notices and package records for this image:" \
        "https://github.com/StormAvenger/buzz-unraid/releases/tag/v${IMAGE_VERSION}" \
        "Dependency sources: ${DEPENDENCY_SOURCES}" \
        "Application patches and build recipes are in this app release source archive." \
        > /usr/share/buzz-container/SOURCE-LOCATION.txt
# Verify the shipped runtime, without any build-only libraries available.
RUN PYTHONDONTWRITEBYTECODE=1 QT_QPA_PLATFORM=offscreen BUZZ_DISABLE_TELEMETRY=1 \
    HF_HUB_DISABLE_TELEMETRY=1 /opt/venv/bin/python /opt/buzz/check-install.py
ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONPATH=/opt/buzz BUZZ_CONTAINER_READINESS=1 \
    USER_ID=99 GROUP_ID=100 UMASK=0002 \
    KEEP_APP_RUNNING=1 WEB_AUDIO=1 WEB_FILE_MANAGER=1 \
    WEB_FILE_MANAGER_ALLOWED_PATHS=/input,/uploads,/output \
    WEB_TERMINAL=0 VNC_LOCALHOST_ONLY=1 \
    BUZZ_MODEL_ROOT=/config/cache/buzz/models \
    HF_HOME=/config/cache/huggingface TORCH_HOME=/config/cache/torch \
    XDG_STATE_HOME=/config/xdg/state \
    BUZZ_OUTPUT_DIRECTORY=/output \
    BUZZ_DISABLE_TELEMETRY=1 HF_HUB_DISABLE_TELEMETRY=1 \
    WANDB_MODE=disabled WANDB_DISABLE_GIT=true \
    BUZZ_FORCE_CPU=false BUZZ_REDUCE_GPU_MEMORY=true \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility \
    QT_X11_NO_MITSHM=1 QT_OPENGL=software PYTHONUNBUFFERED=1
EXPOSE 5800
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD ["/opt/venv/bin/python", "/opt/buzz/healthcheck.py"]
# The GUI base supplies the entrypoint and runs /startapp.sh as USER_ID:GROUP_ID.
