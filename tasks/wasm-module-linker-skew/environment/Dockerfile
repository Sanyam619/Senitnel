# syntax=docker/dockerfile:1

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS gobuilder

WORKDIR /build/gate
COPY gate/go.mod gate/go.sum ./
RUN go mod download
COPY gate/pkg/ pkg/
COPY gate/internal/ internal/
COPY gate/cmd/ cmd/
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/gatectl ./cmd/gatectl

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS rsbuilder

WORKDIR /build/wasm
COPY wasm/Cargo.toml wasm/Cargo.lock ./
COPY wasm/core/Cargo.toml core/
COPY wasm/linkctl/Cargo.toml linkctl/
COPY wasm/core/src/ core/src/
COPY wasm/linkctl/src/ linkctl/src/
RUN cargo generate-lockfile && cargo build --release --locked -p linkctl

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Agent runtime requires tmux and asciinema before any other setup.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tmux asciinema \
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
    && rm -rf /var/lib/apt/lists/*

ENV GOPATH=/go \
    GOCACHE=/tmp/go-cache \
    GOMODCACHE=/go/pkg/mod \
    GOPROXY=off \
    RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo

RUN mkdir -p /go /tmp/go-cache

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY --from=rsbuilder /usr/local/rustup /usr/local/rustup
COPY --from=rsbuilder /usr/local/cargo /usr/local/cargo
COPY --from=rsbuilder /build/wasm/target /app/wasm/target
COPY --from=gobuilder --chmod=755 /out/gatectl /app/bin/gatectl
COPY --from=rsbuilder --chmod=755 /build/wasm/target/release/linkctl /app/bin/linkctl
COPY config/ /app/config/
COPY data/ /app/data/
COPY gate/ /app/gate/
COPY wasm/ /app/wasm/
COPY --from=rsbuilder /build/wasm/Cargo.lock /app/wasm/Cargo.lock
COPY ops/ /app/ops/

ENV PATH="/app/bin:/usr/local/cargo/bin:/usr/local/go/bin:${PATH}"
