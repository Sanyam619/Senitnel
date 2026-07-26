# syntax=docker/dockerfile:1

# Canonical GCC toolchain image (C/C++ tasks; agents compile in-container).
FROM public.ecr.aws/docker/library/gcc:13-bookworm@sha256:930f2ebe239275fa67226654cb79273ea34eee672ae61c8a39f689c37fb7ac5c

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Agent session stack (tmux, asciinema) plus verifier and build deps in one apt transaction.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        bash \
        ca-certificates \
        coreutils \
        libssl-dev \
        procps \
        python3 \
        python3-pip \
        tmux=3.3a-3 \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY include /opt/abdev/include
COPY lib /opt/abdev/lib
COPY tools /opt/abdev/tools
COPY docs /opt/abdev/docs
COPY data /opt/abdev/data
COPY config /opt/abdev/config
COPY Makefile /opt/abdev/Makefile
COPY ops /opt/abdev/ops
COPY packaging /opt/abdev/packaging

RUN make -C /opt/abdev clean all \
    && chmod 755 /opt/abdev/ops/check_image.sh /opt/abdev/ops/reconcile_field.sh

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

WORKDIR /opt/abdev
ENV PATH="/opt/abdev/bin:${PATH}"
