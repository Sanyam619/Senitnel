# syntax=docker/dockerfile:1
#
# Multi-stage: build sealed virtattach on the canonical Go image, then run on
# the canonical Debian bookworm-slim runtime (no toolchain in the agent image).
# Graded work is ops staging under /etc/libvirt and /var/lib/libvirt.

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

WORKDIR /build

COPY go.mod go.sum ./
COPY cmd/ ./cmd/
COPY internal/ ./internal/

RUN mkdir -p /out/bin \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w -buildid=" \
        -o /out/bin/virtattach ./cmd/virtattach

FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.title="libvirt-pool-attach-disk-seating"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        bash \
        ca-certificates=20230311+deb12u1 \
        python-is-python3 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

RUN install -d -m 1777 /tmp \
    && install -d -m 0777 /tmp/.config /tmp/.config/asciinema \
    && test -x /usr/bin/tmux \
    && test -x /usr/bin/asciinema \
    && tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

ENV HOME=/tmp
ENV TMUX_TMPDIR=/tmp
ENV TERM=xterm-256color
ENV XDG_CONFIG_HOME=/tmp/.config
ENV PATH="/app/bin:/app/ops:${PATH}"
ENV QEMU_DIR=/etc/libvirt/qemu
ENV STORAGE_DIR=/etc/libvirt/storage
ENV OPS_DIR=/var/lib/libvirt/ops
ENV POOL_STATE_ROOT=/var/lib/libvirt/storage
ENV LEASE_DIR=/var/run/libvirt
ENV ATTACH_REPORT=/output/libvirt-attach.json

COPY requirements.txt /tmp/requirements.txt
# Installs pytest==8.4.1 and pytest-json-ctrf==0.3.5 with hash-locked transitive deps.
RUN python3 -m pip install --no-cache-dir --break-system-packages --require-hashes \
    -r /tmp/requirements.txt
RUN rm -f /tmp/requirements.txt

COPY --from=builder --chmod=755 /out/bin/virtattach /app/bin/virtattach

COPY docs/ /app/docs/
COPY --chmod=755 ops/ /app/ops/
COPY --chmod=755 stage/ /app/stage/
COPY --chmod=755 tools/virthealth /usr/local/bin/virthealth
COPY etc/libvirt/ /etc/libvirt/
COPY var/lib/libvirt/ /var/lib/libvirt/
COPY var/run/libvirt/ /var/run/libvirt/
COPY data/pools/ /app/data/pools/

RUN mkdir -p /output /var/lib/libvirt/storage /var/lib/libvirt/ops/receipts \
        /var/run/libvirt \
    && chmod 755 /app/ops/*.sh /app/stage/*.sh

WORKDIR /app
