# syntax=docker/dockerfile:1

# Builder stages use sanctioned language images; final runtime is canonical Debian.
FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS rust_builder

ENV PATH="/usr/local/cargo/bin:${PATH}" \
    CARGO_HOME=/usr/local/cargo \
    RUSTUP_HOME=/usr/local/rustup

WORKDIR /build
COPY Cargo.toml Cargo.lock ./
COPY crates/alpha/Cargo.toml crates/alpha/Cargo.toml
COPY cmd/digctl/Cargo.toml cmd/digctl/Cargo.toml
COPY crates/alpha/src/ crates/alpha/src/
COPY cmd/digctl/src/ cmd/digctl/src/
RUN cargo build --release --locked -p digctl

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS go_builder

WORKDIR /build
COPY go.mod go.sum ./
COPY go/ ./go/
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/provcheck ./go/cmd/provcheck \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/polgate ./go/cmd/polgate \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/replayctl ./go/cmd/replayctl

FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Single apt transaction for the final runtime stage (tmux/asciinema required for agent sessions).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        tmux=3.3a-3 \
        ca-certificates=20230311+deb12u1 \
        openssl=3.0.20-1~deb12u2 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        build-essential=12.9 \
        pkg-config=1.8.1-1 \
        libssl-dev=3.0.20-1~deb12u2 \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color \
    LANG=C.UTF-8

RUN command -v tmux \
    && command -v asciinema \
    && tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

# Agent must rebuild after source edits — keep both toolchains in the runtime image.
COPY --from=rust_builder /usr/local/cargo /usr/local/cargo
COPY --from=rust_builder /usr/local/rustup /usr/local/rustup
COPY --from=go_builder /usr/local/go /usr/local/go
ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH="/usr/local/cargo/bin:/usr/local/go/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

COPY --from=rust_builder /build/target/release/digctl /app/bin/digctl
COPY --from=go_builder /out/provcheck /out/polgate /out/replayctl /app/bin/

COPY Cargo.toml Cargo.lock /app/
COPY crates/ /app/crates/
COPY cmd/ /app/cmd/
COPY go.mod go.sum /app/
COPY go/ /app/go/
COPY config/ /app/config/
COPY scripts/ /app/scripts/
COPY data/ /data/

RUN chmod +x /app/bin/* /app/scripts/*.sh \
    && mkdir -p /app/var /output \
    && command -v tmux \
    && command -v asciinema \
    && tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke2 \
    && tmux has-session -t _smoke2 \
    && tmux kill-session -t _smoke2

WORKDIR /app
