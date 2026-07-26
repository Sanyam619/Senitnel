# syntax=docker/dockerfile:1
FROM public.ecr.aws/docker/library/gcc:13-bookworm@sha256:930f2ebe239275fa67226654cb79273ea34eee672ae61c8a39f689c37fb7ac5c

LABEL org.opencontainers.image.source="https://github.com/laude-institute/terminal-bench"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.title="wasm-jit-tierup-reconstruction"
LABEL org.opencontainers.image.description="C WASM tier-up multi-authority admission lab"
LABEL org.opencontainers.image.version="1.0"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        ca-certificates=20230311+deb12u1 \
        make=4.3-4.1 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

COPY wheelhouse/ /tmp/wheelhouse/
COPY requirements.txt /tmp/requirements.txt
# Vendored wheels: pytest, pytest-json-ctrf, and transitive deps.
RUN pip3 install --no-cache-dir --break-system-packages --no-index --find-links=/tmp/wheelhouse -r /tmp/requirements.txt
RUN rm -rf /tmp/wheelhouse /tmp/requirements.txt
RUN ln -sf /usr/bin/python3 /usr/bin/python

WORKDIR /app

COPY Makefile /app/Makefile
COPY README.md /app/README.md
COPY docs/ /app/docs/
COPY include/ /app/include/
COPY src/ /app/src/
COPY --chmod=0755 scripts/run-engine.sh /app/scripts/run-engine.sh
COPY --chmod=0755 scripts/show-coredump.sh /app/scripts/show-coredump.sh
COPY --chmod=0755 scripts/fastcheck /app/scripts/fastcheck
COPY data/ /app/data/

RUN mkdir -p /app/bin /output \
    && ln -sf /app/scripts/fastcheck /app/bin/fastcheck \
    && make clean && make
