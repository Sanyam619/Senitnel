# syntax=docker/dockerfile:1

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS rsbuilder

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

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS gobuilder

WORKDIR /build/lane
COPY lane/go.mod lane/go.sum ./
COPY lane/pkg/ pkg/
COPY lane/internal/ internal/
COPY lane/cmd/ cmd/
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/window ./cmd/window

FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.source="com.hydro.basin-gauge-ops"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        bash \
        ca-certificates=20230311+deb12u1 \
        libutempter0 \
        openssl=3.0.17-1~deb12u2 \
        procps \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        python-is-python3 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux send-keys -t _smoke 'echo tmux_ok' Enter \
    && tmux capture-pane -t _smoke -p | grep -q tmux_ok \
    && tmux kill-session -t _smoke

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY --from=rsbuilder --chmod=755 /build/store/target/release/ctl /app/bin/ctl
COPY --from=gobuilder --chmod=755 /out/window /app/bin/window
COPY config/ /app/config/
COPY data/ /app/data/
COPY store/ /app/store/
COPY lane/ /app/lane/
COPY ops/ /app/ops/

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux send-keys -t _smoke 'echo tmux_ok' Enter \
    && tmux capture-pane -t _smoke -p | grep -q tmux_ok \
    && tmux kill-session -t _smoke

ENV PATH="/app/bin:${PATH}"

WORKDIR /root
