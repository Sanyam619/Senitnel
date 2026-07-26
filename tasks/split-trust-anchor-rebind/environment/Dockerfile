FROM public.ecr.aws/docker/library/gcc:13-bookworm@sha256:930f2ebe239275fa67226654cb79273ea34eee672ae61c8a39f689c37fb7ac5c

LABEL org.opencontainers.image.source="https://github.com/laude-institute/terminal-bench"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.title="split-trust-anchor-rebind"
LABEL org.opencontainers.image.description="C edge-gateway admission environment"
LABEL org.opencontainers.image.version="1.0"

# Agent runtime requires tmux and asciinema before COPY layers below.
# One apt transaction per stage (asciinema/tmux + build/verifier deps).
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

RUN tmux -V && asciinema --version

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

WORKDIR /app

COPY Makefile /app/Makefile
COPY include/ /app/include/
COPY src/ /app/src/
COPY --chmod=0755 scripts/run-admit.sh /app/scripts/run-admit.sh
COPY --chmod=0755 scripts/edge-reload.sh /app/scripts/edge-reload.sh
COPY --chmod=0755 scripts/surfcheck /app/scripts/surfcheck
COPY docs/ /app/docs/
COPY data/ /app/data/

RUN mkdir -p /app/bin /output \
    && ln -sf /app/scripts/surfcheck /app/bin/surfcheck \
    && make clean && make
