# syntax=docker/dockerfile:1

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

ENV TERM=xterm-256color \
    RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH="/app/bin:/app/scripts:/usr/local/cargo/bin:${PATH}" \
    CARGO_TERM_COLOR=never \
    DEBIAN_FRONTEND=noninteractive \
    APP_ROOT=/app \
    LD_LIBRARY_PATH=/app/n4

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        bash \
        build-essential \
        ca-certificates \
        gcc \
        libc6-dev \
        make \
        pkg-config \
        procps \
        python3 \
        python3-pip \
        python-is-python3 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux send-keys -t _smoke 'echo tmux_ok' Enter \
    && tmux capture-pane -t _smoke -p | grep -q tmux_ok \
    && tmux kill-session -t _smoke

# Verifier deps (pytest); allow_internet = false.
RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

WORKDIR /app

COPY Cargo.toml Cargo.lock ./
COPY q7/Cargo.toml q7/Cargo.toml
COPY q7/build.rs q7/build.rs

COPY q7/src/ q7/src/
COPY n4/ n4/
COPY config/ config/
COPY data/ data/
COPY surf/ surf/
COPY eval/ eval/
COPY docs/ docs/
COPY x7/ x7/
COPY scripts/ scripts/

RUN chmod 0755 /app/scripts/build_all.sh \
        /app/eval/run_eval.sh \
        /app/eval/run_surface.sh \
        /app/eval/rebind_checkpoint.sh \
        /app/x7/mesh_m.sh \
    && /app/scripts/build_all.sh

RUN mkdir -p /output
