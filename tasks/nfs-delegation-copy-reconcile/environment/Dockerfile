# syntax=docker/dockerfile:1

# Canonical GCC toolchain image (C/C++ tasks; agents compile in-container).
FROM public.ecr.aws/docker/library/gcc:13-bookworm@sha256:930f2ebe239275fa67226654cb79273ea34eee672ae61c8a39f689c37fb7ac5c

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Agent runtime requires tmux and asciinema before any other setup.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        bash \
        ca-certificates \
        coreutils \
        procps \
        python3 \
        python3-pip \
        python-is-python3 \
        tmux=3.3a-3 \
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

COPY include /app/include
COPY lib /app/lib
COPY tools /app/tools
COPY docs /app/docs
COPY data /app/data
COPY ops /app/ops
COPY config /app/config
COPY packaging /app/packaging
COPY Makefile /app/Makefile
COPY README.md /app/README.md

# Materialise per-episode binary journals from the recorded scenario script.
RUN python3 /app/data/gen_episodes.py \
    && rm -f /app/data/gen_episodes.py

# Build only the read-only inspector. The reconciler is not part of this image.
RUN make -C /app clean bin/nfsr-inspect \
    && sha256sum /app/bin/nfsr-inspect | awk '{print $1}' > /app/packaging/inspect.sha256 \
    && chmod +x /app/ops/*.sh

WORKDIR /app
ENV PATH="/app/bin:${PATH}"
