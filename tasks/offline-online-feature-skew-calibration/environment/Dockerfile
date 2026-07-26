# syntax=docker/dockerfile:1
#
# Final runtime base: canonical Terminal-Bench Rust image
# (dockerfile and image best practices.mdc §2 / ci_checks.mdc).
# Builder uses the same sanctioned digest. The scoring engine builds under
# /app/eng and is re-invoked by the evaluation entrypoint.

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS rsbuilder

WORKDIR /app/eng

# Manifests first (least volatile) so dep resolution caches across source edits.
COPY Cargo.toml Cargo.lock ./
COPY core/Cargo.toml core/Cargo.toml
COPY sx/Cargo.toml sx/Cargo.toml
COPY emit/Cargo.toml emit/Cargo.toml

# Stub sources → fetch (build-time network) → drop stubs before real COPY.
RUN mkdir -p core/src core/seeds sx/src sx/seeds emit/src \
    && echo 'pub fn stub() {}' > core/src/lib.rs \
    && echo 'pub fn stub() {}' > sx/src/lib.rs \
    && echo 'fn main() {}' > core/build.rs \
    && echo 'fn main() {}' > sx/build.rs \
    && echo 'fn main() {}' > emit/src/main.rs \
    && cargo fetch --locked \
    && rm -rf core/src core/seeds core/build.rs sx/src sx/seeds emit/src sx/build.rs

COPY core/ core/
COPY sx/ sx/
COPY emit/ emit/
# Frozen evaluation data and calibration preferences the build scripts read.
COPY data/ /app/data/
COPY calib/ /app/calib/

RUN touch core/src/lib.rs sx/src/lib.rs core/build.rs sx/build.rs emit/src/main.rs \
    && cargo build --release --locked --offline

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.source="terminal-bench-3" \
      org.opencontainers.image.revision="offline-online-feature-skew-calibration" \
      org.opencontainers.image.created="2026-07-25T00:00:00Z" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="MIT"

# OS packages in one layer; pin versions; clean apt lists in the same layer.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        ca-certificates=20230311+deb12u1 \
        python-is-python3 \
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

# Verifier Python dependencies use the hashed lockfile below.
COPY requirements.txt /tmp/requirements.txt
# Installs pytest==8.4.1 and pytest-json-ctrf==0.3.5 with hash-locked transitive deps.
RUN python3 -m pip install --no-cache-dir --break-system-packages --require-hashes \
    -r /tmp/requirements.txt
RUN rm -f /tmp/requirements.txt

# Login shells may drop cargo from PATH — keep toolchain on the default PATH.
RUN ln -sf /usr/local/cargo/bin/cargo /usr/local/bin/cargo \
    && ln -sf /usr/local/cargo/bin/rustc /usr/local/bin/rustc \
    && ln -sf /usr/local/cargo/bin/rustdoc /usr/local/bin/rustdoc

WORKDIR /app

COPY Cargo.toml Cargo.lock /app/eng/
COPY core/ /app/eng/core/
COPY sx/ /app/eng/sx/
COPY emit/ /app/eng/emit/
COPY --from=rsbuilder /app/eng/target /app/eng/target

COPY calib/ /app/calib/
COPY data/ /app/data/
COPY docs/ /app/docs/
COPY eval/ /app/eval/
COPY scripts/ /app/scripts/
COPY tools/ /app/tools/

RUN chmod +x /app/scripts/*.sh /app/tools/feathealth \
    && mkdir -p /output /logs/verifier
