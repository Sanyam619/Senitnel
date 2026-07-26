# syntax=docker/dockerfile:1

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS builder

WORKDIR /build
COPY Cargo.toml ./
COPY stack-core/Cargo.toml stack-core/Cargo.toml
COPY depwalk/Cargo.toml depwalk/Cargo.toml
COPY stackarm/Cargo.toml stackarm/Cargo.toml
COPY ledgersnap/Cargo.toml ledgersnap/Cargo.toml
COPY stack-core/src stack-core/src
COPY depwalk/src depwalk/src
COPY stackarm/src stackarm/src
COPY ledgersnap/src ledgersnap/src

RUN cargo build --release

FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Agent runtime requires tmux and asciinema before any other setup.
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
        ca-certificates=20230311+deb12u1 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        build-essential=12.9 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY --from=builder /usr/local/cargo /usr/local/cargo
COPY --from=builder /usr/local/rustup /usr/local/rustup
ENV PATH="/usr/local/cargo/bin:${PATH}" \
    RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo

COPY --from=builder /build/target /app/target
COPY --from=builder /build/Cargo.lock /app/Cargo.lock
COPY --from=builder --chmod=755 /build/target/release/depwalk /app/bin/chk_a
COPY --from=builder --chmod=755 /build/target/release/stackarm /app/bin/arm_b
COPY --from=builder --chmod=755 /build/target/release/ledgersnap /app/bin/snap_c

COPY config/ /app/config/
COPY --chmod=755 scripts/ /app/scripts/
COPY data/build_fixtures.sh /tmp/build_fixtures.sh

COPY Cargo.toml /app/
COPY stack-core/ /app/stack-core/
COPY depwalk/ /app/depwalk/
COPY stackarm/ /app/stackarm/
COPY ledgersnap/ /app/ledgersnap/

RUN chmod +x /tmp/build_fixtures.sh \
    && /tmp/build_fixtures.sh \
    && rm /tmp/build_fixtures.sh

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

WORKDIR /data
