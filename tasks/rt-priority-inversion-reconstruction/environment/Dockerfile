# syntax=docker/dockerfile:1

# Canonical GCC toolchain image (C/C++ tasks; agents compile in-container).
FROM public.ecr.aws/docker/library/gcc:13-bookworm@sha256:930f2ebe239275fa67226654cb79273ea34eee672ae61c8a39f689c37fb7ac5c

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Agent runtime requires tmux and asciinema before any other setup.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tmux asciinema \
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
        procps \
        python3 \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY include /opt/kernlab/include
COPY src /opt/kernlab/src
COPY kern /opt/kernlab/kern
COPY relay /opt/kernlab/relay
COPY span /opt/kernlab/span
COPY lift /opt/kernlab/lift
COPY config /opt/kernlab/config
COPY traces /opt/kernlab/traces
COPY docs /opt/kernlab/docs
COPY scripts /opt/kernlab/scripts
COPY Makefile /opt/kernlab/Makefile
COPY packaging/klreplay_main.c /tmp/klreplay_main.c

RUN make -C /opt/kernlab kernprobe && make -C /opt/kernlab klreplay-vendor \
    && mkdir -p /opt/kernlab/bin \
    && mv /opt/kernlab/kernprobe /opt/kernlab/klreplay /opt/kernlab/bin/ \
    && rm -f /tmp/klreplay_main.c \
    && chmod +x /opt/kernlab/scripts/smoke.sh \
    && /opt/kernlab/scripts/smoke.sh

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

WORKDIR /opt/kernlab
ENV PATH="/opt/kernlab/bin:${PATH}"
