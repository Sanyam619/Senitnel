# syntax=docker/dockerfile:1
#
# Prebuilt matfan/dmhealth; agent work is ops under /etc/pool and /var.
# Go toolchain remains available for the sanctioned image family, but the
# graded entrypoint is /app/ops/run_materialize.sh (no rebuild required).

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

WORKDIR /build

COPY go.mod ./
COPY Makefile ./
COPY c/ ./c/
COPY cmd/ ./cmd/
COPY internal/ ./internal/

RUN mkdir -p /app/lib /app/bin /out/bin /out/lib \
    && gcc -O2 -fPIC -shared -o /app/lib/libioctl_a.so c/ioctl_a.c \
    && gcc -O2 -fPIC -shared -o /app/lib/libioctl_b.so c/ioctl_b.c \
    && CGO_ENABLED=1 go build -trimpath -ldflags="-s -w" -o /app/bin/matfan ./cmd/matfan \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /app/bin/dmhealth ./cmd/dmhealth \
    && cp /app/bin/matfan /app/bin/dmhealth /out/bin/ \
    && cp /app/lib/libioctl_a.so /app/lib/libioctl_b.so /out/lib/

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.title="dm-thin-snapshot-fanout-reconcile"
LABEL org.opencontainers.image.version="1.1.0"
LABEL org.opencontainers.image.licenses="MIT"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        tmux=3.3a-3 \
        ca-certificates=20230311+deb12u1 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
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
ENV LD_LIBRARY_PATH=/app/lib
ENV PATH="/app/bin:/app/ops:${PATH}"
ENV POOL_ROOT=/var/lib/pool
ENV POOL_SEAL=/etc/pool/pool.seal
ENV DRILL_ROSTER=/etc/pool/drill.roster
ENV LEASE_DIR=/var/run/pool
ENV ORIGIN_ROOT=/var/lib/pool/origin_stage

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY --from=builder --chmod=755 /out/bin/matfan /out/bin/dmhealth /app/bin/
COPY --from=builder --chmod=755 /out/lib/libioctl_a.so /out/lib/libioctl_b.so /app/lib/

COPY docs/ /app/docs/
COPY --chmod=755 ops/ /app/ops/
COPY etc/pool/ /etc/pool/
COPY data/pool/ /var/lib/pool/
COPY data/build_fixtures.py /app/data/build_fixtures.py

RUN mkdir -p /var/run/pool /var/lib/pool/origin_stage /output/drills \
    && chmod 755 /app/ops/*.sh

WORKDIR /app
