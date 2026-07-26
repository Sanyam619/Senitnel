# syntax=docker/dockerfile:1

# Canonical Rust runtime base (dockerfile and image best practices §2).
FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

ENV TERM=xterm-256color \
    RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH="/app/bin:/usr/local/cargo/bin:${PATH}" \
    CARGO_TERM_COLOR=never \
    DEBIAN_FRONTEND=noninteractive

# Agent runtime requires tmux + asciinema; host matrix needs gcc/binutils.
# Toolchains stay in the final image because the solver must rebuild locally.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        bash=5.2.15-2+b7 \
        binutils=2.40-2 \
        build-essential=12.9 \
        ca-certificates=20230311+deb12u1 \
        gcc=4:12.2.0-3 \
        libc6-dev=2.36-9+deb12u10 \
        make=4.3-4.1 \
        pkg-config=1.8.1-1 \
        procps=2:4.0.2-3 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        python-is-python3=3.11.2-1+deb12u1 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux send-keys -t _smoke 'echo tmux_ok' Enter \
    && tmux capture-pane -t _smoke -p | grep -q tmux_ok \
    && tmux kill-session -t _smoke

# Verifier deps are baked into the image (allow_internet = false).
RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

WORKDIR /app

# Project manifests before frequently edited sources (layer cache).
COPY Cargo.toml Cargo.lock ./
COPY k2/Cargo.toml k2/Cargo.toml
COPY n6/Cargo.toml n6/Cargo.toml
COPY n7/Cargo.toml n7/Cargo.toml
COPY q3/Cargo.toml q3/Cargo.toml
COPY q5/Cargo.toml q5/Cargo.toml
COPY k9/Cargo.toml k9/Cargo.toml

# Workspace sources and host/ops surfaces.
COPY k2/src/ k2/src/
COPY n6/src/ n6/src/
COPY n7/src/ n7/src/
COPY q3/build.rs q3/build.rs
COPY q3/src/ q3/src/
COPY q5/build.rs q5/build.rs
COPY q5/src/ q5/src/
COPY k9/src/ k9/src/
COPY hosts/ hosts/
COPY ops/ ops/
COPY link/ link/
COPY pkg/ pkg/
COPY config/ config/
COPY data/ data/
COPY --chmod=0755 tools/abi_probe /app/bin/abi_probe

# Warm/validate the offline Cargo workspace; keep toolchain for agent rebuilds.
RUN cargo build -p q3 -p q5 -p k9 --locked \
    && cargo build -p q3 --release --locked \
    && rm -rf /app/target \
    && rm -rf /usr/local/cargo/registry/src \
    && rm -rf /usr/local/cargo/git/checkouts
