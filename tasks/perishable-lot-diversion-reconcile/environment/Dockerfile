# syntax=docker/dockerfile:1

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS gobuilder

WORKDIR /build/scout
COPY scout/go.mod scout/main.go ./
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" -o /build/scout-bin .

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS rustbuilder

WORKDIR /build/rsrc
COPY src/ ./
RUN rustc --edition=2021 main.rs -O -o /build/ctl

FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Agent session tools + a C toolchain so agents can rebuild /app/bin/ctl after source edits.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        gcc=4:12.2.0-3 \
        libc6-dev=2.36-9+deb12u14 \
        libevent-core-2.1-7=2.1.12-stable-8 \
        libutempter0=1.2.1-3 \
        tmux=3.3a-3 \
    && apt-mark manual \
        tmux asciinema libevent-core-2.1-7 libutempter0 gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/* \
    && install -d -m 1777 /tmp \
    && install -d -m 0777 /root /tmp/.config /tmp/.config/asciinema \
    && test -x /usr/bin/tmux \
    && test -x /usr/bin/asciinema \
    && tmux -V \
    && asciinema --version \
    && HOME=/tmp TMUX_TMPDIR=/tmp TERM=xterm-256color XDG_CONFIG_HOME=/tmp/.config \
        tmux new-session -d -s _tb_image_check sleep 5 \
    && HOME=/tmp TMUX_TMPDIR=/tmp tmux kill-session -t _tb_image_check

ENV HOME=/tmp
ENV TMUX_TMPDIR=/tmp
ENV TERM=xterm-256color
ENV XDG_CONFIG_HOME=/tmp/.config
ENV RUSTUP_HOME=/usr/local/rustup
ENV CARGO_HOME=/usr/local/cargo
ENV PATH=/usr/local/cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

COPY --from=rustbuilder /usr/local/cargo /usr/local/cargo
COPY --from=rustbuilder /usr/local/rustup /usr/local/rustup

RUN python -m pip install --no-cache-dir \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

RUN rustc --version

COPY --from=rustbuilder /build/ctl /app/bin/ctl
COPY --from=gobuilder /build/scout-bin /app/bin/scout
COPY config/ /app/config/
COPY data/ /app/data/
COPY src/ /app/src/
COPY scout/ /app/scout/
COPY ops/ /app/ops/
COPY schemas/ /app/schemas/

WORKDIR /app

# Re-pin tmux/asciinema after COPY layers; verify agent session tools survive image build.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        libevent-core-2.1-7=2.1.12-stable-8 \
        libutempter0=1.2.1-3 \
        tmux=3.3a-3 \
    && apt-mark manual \
        tmux asciinema libevent-core-2.1-7 libutempter0 \
    && rm -rf /var/lib/apt/lists/* \
    && install -d -m 1777 /tmp \
    && install -d -m 0777 /root /tmp/.config /tmp/.config/asciinema \
    && test -x /usr/bin/tmux \
    && test -x /usr/bin/asciinema \
    && tmux -V \
    && asciinema --version \
    && HOME=/tmp TMUX_TMPDIR=/tmp TERM=xterm-256color XDG_CONFIG_HOME=/tmp/.config \
        tmux kill-server 2>/dev/null || true \
    && tmux new-session -d -s _tb_agent_boot sleep 5 \
    && tmux has-session -t _tb_agent_boot \
    && HOME=/tmp TMUX_TMPDIR=/tmp tmux kill-session -t _tb_agent_boot
