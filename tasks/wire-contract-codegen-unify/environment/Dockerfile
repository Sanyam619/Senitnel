# syntax=docker/dockerfile:1
#
# Final runtime base: Terminal-Bench canonical Go
# (public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452...).
# Builder stages use canonical Rust + Go + Eclipse Temurin (JDK family).
# Agent must rebuild Go/Rust/Java offline, so toolchains stay in the final image.

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS rsbuilder

WORKDIR /build/rsx
COPY rsx/Cargo.toml rsx/Cargo.lock ./
COPY rsx/core/Cargo.toml core/
COPY rsx/sievectl/Cargo.toml sievectl/
COPY rsx/core/src/ core/src/
COPY rsx/sievectl/src/ sievectl/src/
RUN cargo build --release --locked -p sievectl

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS gobuilder

WORKDIR /build/gox
COPY gox/go.mod gox/go.sum ./
COPY gox/pkg/ pkg/
COPY gox/internal/ internal/
COPY gox/cmd/ cmd/
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/foldctl ./cmd/foldctl \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/lanehealth ./cmd/lanehealth

WORKDIR /build/xlink
COPY xlink/go.mod ./
COPY xlink/internal/ internal/
COPY xlink/cmd/ cmd/
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/xlink ./cmd/xlink

# Canonical Java (JDK) family — copied into the Go runtime stage below.
FROM public.ecr.aws/docker/library/eclipse-temurin:21-jdk-jammy@sha256:25d1276565738d3c805e632a4542c3a7598866ef967f4def6544c15de3a74b14 AS jdk

# ── Final runtime (canonical Go) ─────────────────────────────────────────────
FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

ENV DEBIAN_FRONTEND=noninteractive \
    TERM=xterm-256color \
    GOPATH=/go \
    GOCACHE=/tmp/go-cache \
    GOMODCACHE=/go/pkg/mod \
    GOPROXY=off \
    RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    JAVA_HOME=/opt/java/openjdk \
    PATH="/app/bin:/usr/local/cargo/bin:/usr/local/go/bin:/opt/java/openjdk/bin:${PATH}"

WORKDIR /app

# 1. OS / agent session tools (single apt transaction; no upgrade).
# Unversioned packages are those whose Debian revision differs across amd64/arm64.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        bash \
        ca-certificates=20230311+deb12u1 \
        make \
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

# 2. Verifier deps (pinned; offline at agent/verifier runtime).
RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

RUN mkdir -p /go /tmp/go-cache /app/bin /app/jvx/classes /output

# 3. Toolchains required for offline agent rebuilds (Rust + JDK from canonical stages).
COPY --from=rsbuilder /usr/local/rustup /usr/local/rustup
COPY --from=rsbuilder /usr/local/cargo /usr/local/cargo
COPY --from=jdk /opt/java/openjdk /opt/java/openjdk

# 4. Stable fixtures / ops / config (less volatile).
COPY idl/ /app/idl/
COPY data/ /app/data/
COPY config/ /app/config/
COPY ops/ /app/ops/

# 5. Language trees (more volatile).
COPY gox/ /app/gox/
COPY rsx/ /app/rsx/
COPY jvx/ /app/jvx/
COPY xlink/ /app/xlink/

# 6. Prebuilt CLIs + lockfile refresh from builders.
COPY --from=gobuilder --chmod=755 /out/foldctl /app/bin/foldctl
COPY --from=gobuilder --chmod=755 /out/lanehealth /app/bin/lanehealth
COPY --from=gobuilder --chmod=755 /out/xlink /app/bin/xlink
COPY --from=rsbuilder --chmod=755 /build/rsx/target/release/sievectl /app/bin/sievectl
COPY --from=rsbuilder /build/rsx/Cargo.lock /app/rsx/Cargo.lock

# 7. Warm Java classes so the initial lane is exerciseable; agent rebuilds after edits.
RUN javac -d /app/jvx/classes \
      /app/jvx/src/main/java/org/lab/p7/EmitC.java \
      /app/jvx/src/main/java/org/lab/p7/SkimEmit.java \
      /app/jvx/src/main/java/org/lab/p7/LaneMain.java \
    && chmod +x /app/ops/scripts/digest_util.py \
    && rustc --version \
    && cargo --version \
    && java -version \
    && javac -version

# 8. Final smoke: session tools + lane entrypoints.
RUN tmux -V \
    && asciinema --version \
    && foldctl >/dev/null \
    && sievectl >/dev/null \
    && java -cp /app/jvx/classes org.lab.p7.LaneMain >/dev/null \
    && lanehealth go \
    && tmux new-session -d -s _smoke2 \
    && tmux has-session -t _smoke2 \
    && tmux kill-session -t _smoke2
