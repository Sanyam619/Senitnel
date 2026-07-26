# syntax=docker/dockerfile:1

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS builder

WORKDIR /build/ws
COPY ws/Cargo.toml ./
COPY ws/m3/Cargo.toml m3/
COPY ws/m7/Cargo.toml m7/
COPY ws/m9/Cargo.toml m9/
COPY ws/m5/Cargo.toml m5/

COPY ws/m3/src m3/src
COPY ws/m7/src m7/src
COPY ws/m9/src m9/src
COPY ws/m5/src m5/src

RUN cargo generate-lockfile \
    && cargo build --release --locked \
    && cargo vendor vendor \
    && mkdir -p .cargo \
    && printf '%s\n' \
        '[source.crates-io]' \
        'replace-with = "vendored-sources"' \
        '' \
        '[source.vendored-sources]' \
        'directory = "vendor"' \
        > .cargo/config.toml

FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Agent runtime requires tmux and asciinema before COPY layers below.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        tmux=3.3a-3 \
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
        ca-certificates=20230311+deb12u1 \
        procps \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        python-is-python3 \
        build-essential=12.9 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY --from=builder /usr/local/cargo /usr/local/cargo
COPY --from=builder /usr/local/rustup /usr/local/rustup
ENV RUSTUP_HOME=/usr/local/rustup
ENV CARGO_HOME=/usr/local/cargo
ENV PATH="/usr/local/cargo/bin:${PATH}"
RUN rustup default 1.85.0

COPY --from=builder /build/ws/target/release/rx-run /app/bin/rx-run
COPY --from=builder /build/ws/Cargo.lock /app/ws/Cargo.lock
COPY --from=builder /build/ws/.cargo /app/ws/.cargo
COPY --from=builder /build/ws/vendor /app/ws/vendor
COPY --from=builder /build/ws/target /app/ws/target
COPY ws/ /app/ws/
COPY data/ /app/data/
COPY ops/ /app/ops/

WORKDIR /app/ws

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke
