# syntax=docker/dockerfile:1

# Canonical GCC toolchain image (C/C++ tasks; agents compile in-container).
FROM public.ecr.aws/docker/library/gcc:13-bookworm@sha256:930f2ebe239275fa67226654cb79273ea34eee672ae61c8a39f689c37fb7ac5c

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Agent runtime requires tmux and asciinema before COPY layers below.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        coreutils \
        libssl-dev \
        procps \
        python3 \
        python3-pip \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY include /opt/kvfs/include
COPY lib /opt/kvfs/lib
COPY tools /opt/kvfs/tools
COPY docs /opt/kvfs/docs
COPY data /opt/kvfs/data
COPY config /opt/kvfs/config
COPY Makefile /opt/kvfs/Makefile
COPY ops /opt/kvfs/ops
COPY packaging /opt/kvfs/packaging

RUN make -C /opt/kvfs clean bin/volpeek \
    && sha256sum /opt/kvfs/bin/volpeek | awk '{print $1}' > /opt/kvfs/packaging/volpeek.sha256 \
    && chmod +x /opt/kvfs/ops/*.sh

WORKDIR /opt/kvfs
ENV PATH="/opt/kvfs/bin:${PATH}"
