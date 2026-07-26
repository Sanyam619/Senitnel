# syntax=docker/dockerfile:1

# Non-canonical base (not ubuntu:24.04). Digest-pinned rust:1.85-slim —
# required: no single approved canonical image covers Rust+Go+C+CMake; agent
# rebuilds Rust in-tree. Submission form: answer No to canonical-base, with
# this multi-language toolchain justification.
FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS rsbuilder

WORKDIR /build
COPY Cargo.toml Cargo.lock ./
COPY config/rust/cargo_config.toml /tmp/cargo_config.toml
RUN mkdir -p .cargo && cp /tmp/cargo_config.toml .cargo/config.toml
COPY r8/Cargo.toml r8/Cargo.toml
COPY r8/build.rs r8/build.rs
COPY r8/src/ r8/src/
RUN FACET_X=0 FACET_Y=0 PACK_WIDTH=8 cargo build -p r8 --locked \
    && FACET_X=0 FACET_Y=0 PACK_WIDTH=8 cargo build -p r8 --release --locked

# Non-canonical runtime base (not ubuntu:24.04). Digest-pinned
# golang:1.24-bookworm — agent rebuilds Rust/Go/CMake in-tree, so both
# toolchains stay in the runtime image by design (same form justification).
FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

ENV TERM=xterm-256color \
    RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH="/app/bin:/usr/local/cargo/bin:/usr/local/go/bin:${PATH}" \
    CARGO_TERM_COLOR=never \
    DEBIAN_FRONTEND=noninteractive \
    GOPATH=/go \
    GOCACHE=/tmp/go-cache \
    GOMODCACHE=/go/pkg/mod \
    GOPROXY=off

# OS packages + agent session tools in one apt transaction per stage.
# Build tools stay in runtime: agent must recompile host/cdylib/cgo/OBJECT.
# Unversioned packages are those whose Debian revision differs across amd64/arm64.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        bash \
        binutils \
        build-essential \
        ca-certificates=20230311+deb12u1 \
        cmake \
        gcc \
        libc6-dev \
        make \
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

# Manifests before frequently edited sources (layer cache).
COPY Cargo.toml Cargo.lock ./
COPY config/rust/cargo_config.toml /tmp/cargo_config.toml
RUN mkdir -p .cargo && cp /tmp/cargo_config.toml .cargo/config.toml
COPY r8/Cargo.toml r8/Cargo.toml
COPY g4/go.mod g4/go.mod

# Workspace sources and ops surfaces.
COPY r8/build.rs r8/build.rs
COPY r8/src/ r8/src/
COPY g4/ g4/
COPY c6/ c6/
COPY gen/ gen/
COPY host/ host/
COPY ops/matrix.toml ops/matrix.toml
COPY ops/runbooks/ ops/runbooks/
COPY ops/nx/ ops/nx/
COPY --chmod=0755 ops/status_check.sh ops/status_check.sh
COPY link/ link/
COPY config/ config/
COPY data/ data/
# Probe sources are build-context only: compile under /app then strip so the
# runtime image has no readable stamp algebra (binary + probe.stamp only).
COPY tools/unify_probe/ /app/_probe_src/

RUN mkdir -p /go /tmp/go-cache /app/bin /app/include /app/ops \
    && cd /app/g4 && go build -o /app/bin/slotctl . \
    && cmake -S /app/gen -B /tmp/genbuild && cmake --build /tmp/genbuild \
    && cp /tmp/genbuild/hdrgen /app/bin/hdrgen \
    && cd /app/_probe_src \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-buildid=" -o /app/bin/unify_probe . \
    && cd /app && rm -rf /app/_probe_src \
    && sha256sum /app/bin/unify_probe | awk '{print $1}' > /app/ops/probe.stamp \
    && chmod 0755 /app/bin/slotctl /app/bin/hdrgen /app/bin/unify_probe \
    && FACET_X=0 FACET_Y=0 PACK_WIDTH=8 cargo build -p r8 --locked \
    && FACET_X=0 FACET_Y=0 PACK_WIDTH=8 cargo build -p r8 --release --locked \
    && rm -rf /app/target /tmp/genbuild \
    && rm -rf /usr/local/cargo/registry/src \
    && rm -rf /usr/local/cargo/git/checkouts
