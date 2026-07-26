# syntax=docker/dockerfile:1
#
# Prebuilt ringfan/preflight/healthctl; agent work is ops under /etc/ingest
# and /var/lib/ingest. Graded entrypoint is /app/ops/run_cutover.sh.
# Go sources are builder-only and are not copied into the final image.

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

WORKDIR /build
COPY go.mod ./
COPY cmd/ ./cmd/
RUN mkdir -p /out/bin \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/bin/ringfan ./cmd/ringfan \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/bin/preflight ./cmd/preflight \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/bin/healthctl ./cmd/healthctl

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.title="iouring-registered-buffer-lease-cutover"
LABEL org.opencontainers.image.version="2.1.0"
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
ENV PATH="/app/bin:/app/ops:/app/mesh:/app/seat:/app/arm:/app/rim:${PATH}"

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY --from=builder --chmod=755 /out/bin/ringfan /out/bin/preflight /out/bin/healthctl /app/bin/
COPY docs/ /app/docs/
COPY --chmod=755 ops/ /app/ops/
COPY --chmod=755 mesh/ /app/mesh/
COPY --chmod=755 seat/ /app/seat/
COPY --chmod=755 arm/ /app/arm/
COPY --chmod=755 rim/ /app/rim/
COPY etc/ingest/ /etc/ingest/
COPY data/ingest/ /var/lib/ingest/

RUN mkdir -p /output /var/lib/ingest/mnt/broker/ten /var/lib/ingest/mnt/host/ten \
        /var/lib/ingest/ring/broker/slots /var/lib/ingest/preflight \
        /etc/ingest/units/abort.d \
    && chmod 755 /app/ops/*.sh /app/mesh/*.sh /app/seat/*.sh /app/arm/*.sh /app/rim/*.sh \
    && rm -f /var/lib/ingest/mnt/broker/ten/.keep

WORKDIR /app
