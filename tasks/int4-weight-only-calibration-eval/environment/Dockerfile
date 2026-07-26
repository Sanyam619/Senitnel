# syntax=docker/dockerfile:1

# Canonical Terminal-Bench Rust image, pinned to the approved digest.
FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS rsbuilder

WORKDIR /app/eng

COPY eng/Cargo.toml eng/Cargo.lock ./
COPY eng/core/Cargo.toml core/Cargo.toml
COPY eng/knit/Cargo.toml knit/Cargo.toml
COPY eng/pane/Cargo.toml pane/Cargo.toml
COPY eng/emit/Cargo.toml emit/Cargo.toml

# The seating gates in core/build.rs, knit/build.rs and pane/build.rs read the
# acceptance receipt and the registry at compile time.
COPY serving/ /app/serving/
COPY data/ /app/data/
COPY eng/seeds/ seeds/
COPY eng/core/ core/
COPY eng/knit/ knit/
COPY eng/pane/ pane/
COPY eng/emit/ emit/

# The workspace is std-only, so the locked build requires no network.
RUN cargo build --release --locked --offline

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.source="terminal-bench-3" \
      org.opencontainers.image.revision="int4-weight-only-calibration-eval" \
      org.opencontainers.image.created="2026-07-26T00:00:00Z" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="MIT"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
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

COPY eng/Cargo.toml eng/Cargo.lock /app/eng/
COPY eng/seeds/ /app/eng/seeds/
COPY eng/core/ /app/eng/core/
COPY eng/knit/ /app/eng/knit/
COPY eng/pane/ /app/eng/pane/
COPY eng/emit/ /app/eng/emit/
COPY --from=rsbuilder /app/eng/target /app/eng/target

COPY calib/ /app/calib/
COPY serving/ /app/serving/
COPY --chmod=0755 scripts/ /app/scripts/
COPY docs/ /app/docs/
COPY data/ /app/data/

RUN mkdir -p /output /logs/verifier
