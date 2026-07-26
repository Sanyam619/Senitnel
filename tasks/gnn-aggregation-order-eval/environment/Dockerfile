# syntax=docker/dockerfile:1
#
# Builder + final runtime both use the sanctioned Terminal-Bench Rust
# canonical image (dockerfile and image best practices §2):
#   public.ecr.aws/docker/library/rust:1.85-slim
#   @sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36
#
# Final stage keeps the Rust toolchain because the agent/verifier rebuild
# /app/eng on every eval run (best practices §6 / §7).

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS rsbuilder

WORKDIR /app/eng

# Manifests first (least volatile), then sources (best practices §4).
COPY Cargo.toml Cargo.lock ./
COPY core/Cargo.toml core/Cargo.toml
COPY rank/Cargo.toml rank/Cargo.toml
COPY emit/Cargo.toml emit/Cargo.toml

# build.rs reads calib + feature_registry during compile.
COPY calib/ /app/calib/
COPY data/ /app/data/
COPY core/ core/
COPY rank/ rank/
COPY emit/ emit/

# Workspace is std-only; locked offline build needs no network (§3 / §7).
RUN cargo build --release --locked --offline

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.source="terminal-bench-3" \
      org.opencontainers.image.revision="gnn-aggregation-order-eval" \
      org.opencontainers.image.created="2026-07-25T00:00:00Z" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="MIT"

# One apt transaction; pin versions; clean lists in the same layer (§5).
# tmux + asciinema are required agent session tools (§7 / docker environment.mdc).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        bash \
        ca-certificates=20230311+deb12u1 \
        python-is-python3=3.11.2-1+deb12u1 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color \
    RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH="/usr/local/cargo/bin:${PATH}" \
    CARGO_NET_OFFLINE=true

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

COPY requirements.txt /tmp/requirements.txt
# Installs pytest==8.4.1 and pytest-json-ctrf==0.3.5 with hash-locked transitive deps.
RUN python3 -m pip install --no-cache-dir --break-system-packages --require-hashes \
    -r /tmp/requirements.txt
RUN rm -f /tmp/requirements.txt

# Login shells reset PATH and drop /usr/local/cargo/bin — keep cargo reachable.
RUN ln -sf /usr/local/cargo/bin/cargo /usr/local/bin/cargo \
    && ln -sf /usr/local/cargo/bin/rustc /usr/local/bin/rustc \
    && ln -sf /usr/local/cargo/bin/rustdoc /usr/local/bin/rustdoc

WORKDIR /app

# Narrow COPY paths only (best practices §9); never COPY solution/ or tests/.
COPY Cargo.toml Cargo.lock /app/eng/
COPY core/ /app/eng/core/
COPY rank/ /app/eng/rank/
COPY emit/ /app/eng/emit/
COPY --from=rsbuilder /app/eng/target /app/eng/target

COPY calib/ /app/calib/
COPY eval/ /app/eval/
COPY --chmod=0755 scripts/ /app/scripts/
COPY docs/ /app/docs/
COPY data/ /app/data/

RUN mkdir -p /output /logs/verifier
