# syntax=docker/dockerfile:1
#
# Final runtime base: canonical Debian (Dockerfile & Image Best Practices).
# Builder stage donates digest-pinned Rust toolchain + prebuilt binaries so
# agents can rebuild offline (allow_internet = false).

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS rsbuilder

ENV PATH="/usr/local/cargo/bin:${PATH}"

WORKDIR /build
COPY Cargo.toml Cargo.lock ./
COPY core/Cargo.toml core/
COPY vfy/Cargo.toml vfy/
COPY skim/Cargo.toml skim/
COPY vfy/build.rs vfy/
COPY vfy/seeds/ vfy/seeds/
COPY core/src/ core/src/
COPY vfy/src/ vfy/src/
COPY skim/src/ skim/src/
RUN cargo build -p trusteval -p skim --release --locked

FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        bash \
        build-essential=12.9 \
        ca-certificates=20230311+deb12u1 \
        python-is-python3 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color \
    RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH="/usr/local/cargo/bin:/app/bin:${PATH}" \
    CARGO_NET_OFFLINE=true

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

COPY requirements.txt /tmp/requirements.txt
# Installs pytest, pytest-json-ctrf, and pytest-randomly with hash-locked dependencies.
RUN python3 -m pip install --no-cache-dir --break-system-packages --require-hashes \
    -r /tmp/requirements.txt
RUN rm -f /tmp/requirements.txt

WORKDIR /app

COPY --from=rsbuilder /usr/local/cargo /usr/local/cargo
COPY --from=rsbuilder /usr/local/rustup /usr/local/rustup
COPY --from=rsbuilder /build/target /app/target
COPY --from=rsbuilder --chmod=755 /build/target/release/trusteval /app/bin/trusteval
COPY --from=rsbuilder --chmod=755 /build/target/release/surfskim /app/bin/surfskim

RUN rustup default 1.85.0 \
    && ln -sf /usr/local/cargo/bin/cargo /usr/local/bin/cargo \
    && ln -sf /usr/local/cargo/bin/rustc /usr/local/bin/rustc \
    && ln -sf /usr/local/cargo/bin/rustdoc /usr/local/bin/rustdoc \
    && ln -sf /usr/local/cargo/bin/rustup /usr/local/bin/rustup

COPY Cargo.toml Cargo.lock /app/
COPY core/ /app/core/
COPY vfy/ /app/vfy/
COPY skim/ /app/skim/
COPY config/ /app/config/
COPY data/ /app/data/
COPY ops/ /app/ops/

RUN chmod +x /app/ops/run_mesh_attest.sh \
    && mkdir -p /output
