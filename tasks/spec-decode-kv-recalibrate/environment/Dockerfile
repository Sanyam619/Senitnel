# syntax=docker/dockerfile:1

# No canonical Rust base image exists; rust:1.85-slim is digest-pinned.
# The builder compiles the crate and supplies the toolchain for the runtime stage.
FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS builder

WORKDIR /build/eng

COPY engine/Cargo.toml engine/Cargo.lock ./
COPY engine/src/ src/

# Std-only crate with zero external dependencies; --offline is safe.
RUN cargo build --release --locked --offline

FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.source="terminal-bench-3" \
      org.opencontainers.image.revision="spec-decode-kv-recalibrate" \
      org.opencontainers.image.created="2026-07-12T00:00:00Z" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="MIT"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        tmux=3.3a-3 \
        ca-certificates=20230311+deb12u1 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        python-is-python3=3.11.2-1+deb12u1 \
        build-essential=12.9 \
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

# Install the Rust toolchain into the runtime image so the agent can
# rebuild the engine crate offline after editing it.
COPY --from=builder /usr/local/cargo /usr/local/cargo
COPY --from=builder /usr/local/rustup /usr/local/rustup
ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:${PATH}

COPY engine/ /app/eng/
COPY --from=builder /build/eng/target/release/spec-eval /app/eng/target/release/spec-eval

COPY data/ /app/data/
COPY docs/ /app/docs/
COPY scripts/ /app/scripts/
RUN chmod +x /app/scripts/*.sh

WORKDIR /app

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke
