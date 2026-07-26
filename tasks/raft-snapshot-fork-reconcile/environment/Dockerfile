# syntax=docker/dockerfile:1

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS go_builder

WORKDIR /build/lane
COPY lane/go.mod lane/go.sum ./
RUN go mod download
COPY lane/pkg/frame/row.go pkg/frame/row.go
COPY lane/internal/m7/ internal/m7/
COPY lane/cmd/lane/ cmd/lane/
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /lane ./cmd/lane

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS rust_builder

WORKDIR /build/store

COPY store/Cargo.toml store/Cargo.lock ./
COPY store/manifest/Cargo.toml manifest/
COPY store/wal/Cargo.toml wal/
COPY store/index/Cargo.toml index/
COPY store/ops/Cargo.toml ops/
COPY store/ctl/Cargo.toml ctl/

COPY store/src/ src/
COPY store/manifest/src/ manifest/src/
COPY store/wal/src/ wal/src/
COPY store/index/src/ index/src/
COPY store/ops/src/ ops/src/
COPY store/ctl/src/ ctl/src/

RUN cargo build --release --locked -p ctl

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
    GOPROXY=off
RUN mkdir -p /go /tmp/go-cache

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY --from=rust_builder --chmod=755 /build/store/target/release/ctl /app/bin/ctl
COPY --from=go_builder --chmod=755 /lane /app/bin/lane
COPY config/ /app/config/
COPY data/ /app/data/
COPY store/ /app/store/
COPY lane/ /app/lane/
COPY ops/ /app/ops/

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

WORKDIR /app
ENV PATH="/app/bin:${PATH}"
