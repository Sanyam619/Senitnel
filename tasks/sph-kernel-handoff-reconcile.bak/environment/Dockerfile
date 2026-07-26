# syntax=docker/dockerfile:1

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS builder

WORKDIR /build/ws
COPY ws/Cargo.toml ./
COPY ws/sph_core/Cargo.toml sph_core/
COPY ws/sph_kernels/Cargo.toml sph_kernels/
COPY ws/sph_a/Cargo.toml sph_a/
COPY ws/sph_d/Cargo.toml sph_d/
COPY ws/sph_b/Cargo.toml sph_b/
COPY ws/sph_c/Cargo.toml sph_c/
COPY ws/sph_runner/Cargo.toml sph_runner/
COPY ws/sph_verify/Cargo.toml sph_verify/

COPY ws/sph_core/src sph_core/src
COPY ws/sph_kernels/src sph_kernels/src
COPY ws/sph_a/src sph_a/src
COPY ws/sph_d/src sph_d/src
COPY ws/sph_b/src sph_b/src
COPY ws/sph_c/src sph_c/src
COPY ws/sph_runner/src sph_runner/src
COPY ws/sph_verify/src sph_verify/src

RUN cargo generate-lockfile \
    && cargo build --release --locked

FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

ENV TERM=xterm-256color

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        bash \
        build-essential=12.9 \
        ca-certificates=20230311+deb12u1 \
        procps \
        python-is-python3 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/* \
    && tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY --from=builder /usr/local/cargo /usr/local/cargo
COPY --from=builder /usr/local/rustup /usr/local/rustup
ENV RUSTUP_HOME=/usr/local/rustup
ENV CARGO_HOME=/usr/local/cargo
ENV PATH="/usr/local/cargo/bin:${PATH}"
RUN rustup default 1.85.0

RUN mkdir -p /app/bin /output /logs/verifier
# /app/bin holds the runner artifact /app/bin/sph-run.
# /logs/verifier collects the verifier-side build logs sph-run-build.log,
# sph-run.log, and sph-verify-build.log, plus the verifier-owned sph-verify
# binary rebuilt from tests/rustcheck/main.rs on every session, so a failed
# rebuild can be inspected.

COPY --from=builder /build/ws/target/release/sph-run /app/bin/sph-run
COPY --from=builder /build/ws/Cargo.lock /app/ws/Cargo.lock
COPY --from=builder /build/ws/target /app/ws/target
COPY ws/ /app/ws/
COPY data/ /app/data/
COPY docs/ /app/docs/
COPY scripts/ /app/scripts/

RUN chmod +x /app/scripts/*.sh

WORKDIR /app
