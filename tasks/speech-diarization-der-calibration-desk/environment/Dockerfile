# syntax=docker/dockerfile:1
#
# Builder + final runtime both use the sanctioned Terminal-Bench Rust
# canonical image (dockerfile and image best practices §2).

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS builder

WORKDIR /build/eng

COPY eng/Cargo.toml eng/Cargo.lock eng/build.rs ./
COPY eng/stub_main.rs /tmp/stub_main.rs
# Manifest-first fetch so source edits do not bust the dep layer.
RUN mkdir -p src \
    && cp /tmp/stub_main.rs src/main.rs \
    && cargo fetch --locked \
    && rm -rf src
COPY eng/seeds/ seeds/
COPY eng/src/ src/
COPY seat/ /build/seat/
COPY flag/ /build/flag/
COPY mix/ /build/mix/
COPY score/ /build/score/
COPY gate/ /build/gate/
COPY calib/ /build/calib/
COPY data/embed_registry/ /build/data/embed_registry/
COPY data/cluster_registry/ /build/data/cluster_registry/
RUN cargo build --release --locked --offline

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.source="terminal-bench-3" \
      org.opencontainers.image.revision="speech-diarization-der-calibration-desk" \
      org.opencontainers.image.created="2026-07-26T00:00:00Z" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="MIT"

# One apt transaction; pin versions; clean lists in the same layer.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        bash=5.2.15-2+b7 \
        ca-certificates=20230311+deb12u1 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        python-is-python3=3.11.2-1+deb12u1 \
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

WORKDIR /app

# Keep cargo on PATH for non-login shells that reset ENV.
RUN ln -sf /usr/local/cargo/bin/cargo /usr/local/bin/cargo \
    && ln -sf /usr/local/cargo/bin/rustc /usr/local/bin/rustc \
    && ln -sf /usr/local/cargo/bin/rustdoc /usr/local/bin/rustdoc

COPY eng/ /app/eng/
COPY calib/ /app/calib/
COPY seat/ /app/seat/
COPY flag/ /app/flag/
COPY mix/ /app/mix/
COPY score/ /app/score/
COPY gate/ /app/gate/
# Graded binary path after rebuild: /app/eng/target/release/diar-eval
COPY --from=builder --chmod=0755 /build/eng/target/release/diar-eval /app/eng/target/release/diar-eval

COPY data/ /app/data/
COPY docs/ /app/docs/
COPY --chmod=0755 scripts/run_diar_eval.sh /app/scripts/run_diar_eval.sh
COPY --chmod=0755 scripts/verify_fixtures.sh /app/scripts/verify_fixtures.sh
COPY --chmod=0755 tools/diarprobe /app/tools/diarprobe
COPY tools/probe_calc.py /app/tools/probe_calc.py

RUN mkdir -p /output /logs/verifier
