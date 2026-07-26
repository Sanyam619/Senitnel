# syntax=docker/dockerfile:1

FROM public.ecr.aws/docker/library/eclipse-temurin:21-jdk-jammy@sha256:25d1276565738d3c805e632a4542c3a7598866ef967f4def6544c15de3a74b14

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Agent session stack (tmux, asciinema) plus verifier runtime in one apt transaction.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema \
        bash \
        ca-certificates \
        libutempter0 \
        procps \
        python3 \
        python3-pip \
        tmux \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

ENV TERM=xterm-256color \
    APP_ROOT=/app \
    PATH="/app/scripts:${PATH}"

RUN mkdir -p /app /output \
    && tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

# Copy sources into the runtime location the agent will see.
COPY src     /app/src
COPY scripts /app/scripts
COPY docs    /app/docs
COPY config  /app/config

RUN chmod +x /app/scripts/*.sh

# Compile once so the runtime image already has classes; the driver's own
# runner rebuilds anyway before executing.
RUN bash /app/scripts/build.sh

# Regenerate the deterministic dataset (bases/adapters/eval) from seeds.json
# using the compiled DataGenerator so agents inspecting /app/data see the
# exact bytes the pipeline will consume. Then drop the generator source and
# class so the fixture-construction math is not sitting next to AlignPolicy.
RUN bash /app/scripts/generate_fixtures.sh \
    && rm -f /app/src/main/java/io/terminus/stitch/io/DataGenerator.java \
    && rm -f /app/build/classes/io/terminus/stitch/io/DataGenerator.class \
    && bash /app/scripts/build.sh

WORKDIR /app
