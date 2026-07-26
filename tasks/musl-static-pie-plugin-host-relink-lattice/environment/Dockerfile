# syntax=docker/dockerfile:1

# Builder: canonical Rust toolchain (digest-pinned).
FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS rsbuilder

WORKDIR /build
COPY Cargo.toml Cargo.lock ./
COPY k2/Cargo.toml k2/Cargo.toml
COPY p7/Cargo.toml p7/Cargo.toml
COPY k2/src/ k2/src/
COPY p7/src/ p7/src/
RUN cargo build -p p7 --locked \
    && cargo build -p p7 --release --locked

# Final runtime: canonical Go bookworm (digest-pinned). Agent rebuilds C/Rust/Go
# in-tree, so toolchains stay in the runtime image by design.
FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

LABEL org.opencontainers.image.source="gateway-lattice"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

ENV TERM=xterm-256color \
    RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH="/usr/local/cargo/bin:/usr/local/go/bin:/usr/bin:/bin:/app/tools" \
    LATTICE_SAFE_PATH="/usr/local/cargo/bin:/usr/local/go/bin:/usr/bin:/bin" \
    GO_BIN="/usr/local/go/bin/go" \
    CARGO_TERM_COLOR=never \
    DEBIAN_FRONTEND=noninteractive \
    GOPATH=/go \
    GOCACHE=/tmp/go-cache \
    GOMODCACHE=/go/pkg/mod \
    GOPROXY=off

# OS packages + agent session tools in one apt transaction per stage.
# Build tools stay in runtime: agent must recompile host/plugin/supervisor.
# Unversioned packages are those whose Debian revision differs across amd64/arm64.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        bash \
        binutils \
        build-essential \
        ca-certificates=20230311+deb12u1 \
        gcc \
        libc6-dev \
        make \
        musl-tools \
        pkg-config \
        procps \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        python-is-python3 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux send-keys -t _smoke 'echo tmux_ok' Enter \
    && tmux capture-pane -t _smoke -p | grep -q tmux_ok \
    && tmux kill-session -t _smoke

# Verifier deps baked into the image (allow_internet = false).
RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY --from=rsbuilder /usr/local/rustup /usr/local/rustup
COPY --from=rsbuilder /usr/local/cargo /usr/local/cargo

WORKDIR /app

# Manifests before frequently edited sources.
COPY Cargo.toml Cargo.lock ./
COPY k2/Cargo.toml k2/Cargo.toml
COPY p7/Cargo.toml p7/Cargo.toml
COPY g3/go.mod g3/go.sum g3/
COPY k2/src/ k2/src/
COPY p7/src/ p7/src/
COPY h4/ h4/
COPY g3/emit_xv.go g3/main.go g3/preview_cg.go g3/
COPY include/ include/
COPY ops/matrix.toml /app/ops/matrix.toml
COPY ops/runbooks/ /app/ops/runbooks/
COPY --chmod=0755 ops/status_check.sh /app/ops/status_check.sh
COPY link/ link/
COPY config/ config/
COPY data/ data/
COPY tools/probe/ /app/tools/probe/

# Materialize Cargo workspace config from a non-hidden seed. Platforms that
# strip archive dot-directories would fail a context COPY of .cargo/; Cargo
# still reads /.cargo/config.toml at build time.
RUN mkdir -p /app/.cargo \
    && cp /app/config/rust/cargo_config.toml /app/.cargo/config.toml

# Compile the observation probe only. Agent rebuilds host/plugin crates in-tree;
# skip image-time cargo builds to keep environment start under build_timeout.
RUN mkdir -p /go /tmp/go-cache /app/tools \
    && cd /app/tools/probe \
    && go build -o /app/tools/lattice_probe . \
    && chmod 0755 /app/tools/lattice_probe \
    && cd /app/g3 && go build -o /tmp/g3smoke . && rm -f /tmp/g3smoke \
    && rm -rf /usr/local/cargo/registry/src \
    && rm -rf /usr/local/cargo/git/checkouts
