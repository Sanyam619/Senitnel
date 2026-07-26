# syntax=docker/dockerfile:1
#
# Canonical Terminal-Bench bases (dockerfile and image best practices.mdc §2):
# - Builder: rust:1.85-slim (Rust family)
# - Final runtime: golang:1.24-bookworm (Go family; agent rebuilds Rust/Go/CMake in-tree)

# Builder: warm/validate the staticlib; agent rebuilds in-tree at runtime.
FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS rsbuilder

WORKDIR /build
COPY Cargo.toml Cargo.lock ./
COPY config/rust/cargo_config.toml /tmp/cargo_config.toml
RUN mkdir -p .cargo && cp /tmp/cargo_config.toml .cargo/config.toml
COPY r7/Cargo.toml r7/Cargo.toml
COPY r7/build.rs r7/build.rs
COPY r7/src/ r7/src/
RUN STRAND_A=0 STRAND_B=0 BITCODE_EPOCH=3 cargo build -p r7 --locked \
    && STRAND_A=0 STRAND_B=0 BITCODE_EPOCH=3 cargo build -p r7 --release --locked

# Final runtime: sanctioned golang base — keeps Go + hosts Rust via COPY --from.
FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.revision="thin-lto-archive-visibility-lattice"
LABEL org.opencontainers.image.created="2026-07-20"
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

# One apt transaction; versions pinned to bookworm Candidates on this digest.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        bash=5.2.15-2+b13 \
        binutils=2.40-2 \
        build-essential=12.9 \
        ca-certificates=20230311+deb12u1 \
        cmake=3.25.1-1 \
        gcc=4:12.2.0-3 \
        libc6-dev=2.36-9+deb12u14 \
        make=4.3-4.1 \
        pkg-config=1.8.1-1 \
        procps=2:4.0.2-3 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        python-is-python3=3.11.2-1+deb12u1 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux send-keys -t _smoke 'echo tmux_ok' Enter \
    && tmux capture-pane -t _smoke -p | grep -q tmux_ok \
    && tmux kill-session -t _smoke

# Verifier deps baked in (allow_internet = false; no runtime installs in test.sh).
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
COPY r7/Cargo.toml r7/Cargo.toml
COPY g5/go.mod g5/go.sum g5/

COPY r7/build.rs r7/build.rs
COPY r7/src/ r7/src/
COPY g5/ g5/
COPY c9/ c9/
COPY vis/ vis/
COPY host/ host/
COPY ops/matrix.toml ops/matrix.toml
COPY ops/nx/ ops/nx/
COPY ops/runbooks/ ops/runbooks/
COPY --chmod=0755 ops/status_check.sh ops/status_check.sh
COPY link/ link/
COPY config/ config/
COPY data/ data/
# Probe sources are build-context only: compile then strip so the runtime
# image has no readable digest algebra (binary + probe.stamp only).
COPY tools/lattice_probe/ /app/_probe_src/

RUN mkdir -p /go /tmp/go-cache /app/bin /app/include /app/ops /app/config/lane.d \
    && cd /app/g5 && go build -o /app/bin/archctl . \
    && cmake -S /app/vis -B /tmp/visbuild && cmake --build /tmp/visbuild \
    && cp /tmp/visbuild/visgen /app/bin/visgen \
    && cd /app/_probe_src && go build -o /app/bin/lattice_probe . \
    && cd /app && rm -rf /app/_probe_src \
    && sha256sum /app/bin/lattice_probe | awk '{print $1}' > /app/ops/probe.stamp \
    && chmod 0755 /app/bin/archctl /app/bin/visgen /app/bin/lattice_probe \
    && STRAND_A=0 STRAND_B=0 BITCODE_EPOCH=3 ARCHIVE_MEMBERS=4 cargo build -p r7 --locked \
    && STRAND_A=0 STRAND_B=0 BITCODE_EPOCH=3 ARCHIVE_MEMBERS=4 cargo build -p r7 --release --locked \
    && rm -rf /app/target /tmp/visbuild \
    && rm -rf /usr/local/cargo/registry/src \
    && rm -rf /usr/local/cargo/git/checkouts
