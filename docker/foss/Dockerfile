# syntax=docker/dockerfile:1

# FOSS + social PAI + ProjectDiscovery tools
# Fast rebuilds: DOCKER_BUILDKIT=1 docker compose build foss

FROM python:3.12-slim-bookworm

ARG TARGETARCH=amd64

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SPIDERFOOT_DIR=/tools/spiderfoot \
    PHOTON_DIR=/tools/Photon

# System deps — apt cache mount speeds rebuilds
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl unzip git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tools

# Social PAI — single cached pip layer (changes rarely)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install \
    sherlock-project \
    holehe \
    maigret \
    socialscan \
    ignorant

# SpiderFoot — shallow clone, pip cache, drop .git to shrink layer
RUN --mount=type=cache,target=/root/.cache/pip \
    git clone --depth 1 https://github.com/smicallef/spiderfoot.git /tools/spiderfoot \
    && pip install -r /tools/spiderfoot/requirements.txt \
    && rm -rf /tools/spiderfoot/.git

# Photon
RUN --mount=type=cache,target=/root/.cache/pip \
    git clone --depth 1 https://github.com/s0md3v/Photon.git /tools/Photon \
    && pip install -r /tools/Photon/requirements.txt \
    && rm -rf /tools/Photon/.git

# ProjectDiscovery binaries — parallel download + unzip
RUN set -eux; \
    arch="${TARGETARCH:-amd64}"; \
    mkdir -p /usr/local/bin /tmp/pd; \
    for spec in subfinder:2.6.7 dnsx:1.2.1 httpx:1.6.9 tlsx:1.1.9; do \
      ( \
        name="${spec%%:*}"; ver="${spec##*:}"; \
        curl -fsSL "https://github.com/projectdiscovery/${name}/releases/download/v${ver}/${name}_${ver}_linux_${arch}.zip" \
          -o "/tmp/pd/${name}.zip"; \
        unzip -oq "/tmp/pd/${name}.zip" -d /usr/local/bin/; \
        chmod +x "/usr/local/bin/${name}"; \
      ) & \
    done; \
    wait; \
    rm -rf /tmp/pd

VOLUME ["/output"]
CMD ["sleep", "infinity"]
