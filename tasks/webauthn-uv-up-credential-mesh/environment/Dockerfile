# syntax=docker/dockerfile:1
#
# Multi-stage: Rust builder (sanctioned) compiles sealed binaries; final
# runtime is the sanctioned Python canonical image (verifier + bash ops).
# See `dockerfile and image best practices.mdc` §2 and `docker environment.mdc`.

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS rsbuilder

ENV PATH="/usr/local/cargo/bin:${PATH}"

WORKDIR /build
COPY Cargo.toml Cargo.lock ./
COPY core/Cargo.toml core/
COPY vfy/Cargo.toml vfy/
COPY skim/Cargo.toml skim/
# Manifest-first fetch so source edits do not bust the dep layer.
RUN mkdir -p core/src vfy/src skim/src \
    && printf '#![allow(dead_code)]\n' > core/src/lib.rs \
    && printf 'fn main() {}\n' > vfy/src/main.rs \
    && printf 'fn main() {}\n' > skim/src/main.rs \
    && cargo fetch --locked
COPY core/src/ core/src/
COPY vfy/src/ vfy/src/
COPY skim/src/ skim/src/
RUN cargo build -p trusteval -p skim --release --locked \
    && cp /build/target/release/trusteval /build/trusteval.bin \
    && cp /build/target/release/jarcheck /build/jarcheck.bin \
    && rm -rf /build/target /build/core /build/vfy /build/skim \
        /build/Cargo.toml /build/Cargo.lock

FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

LABEL org.opencontainers.image.source="terminal-bench-3" \
      org.opencontainers.image.revision="webauthn-uv-up-credential-mesh" \
      org.opencontainers.image.created="2026-07-26T00:00:00Z" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="MIT"

# One apt transaction; pin versions; clean lists in the same layer.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        ca-certificates=20230311+deb12u1 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color \
    HOME=/tmp \
    PATH="/app/bin:${PATH}"

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke \
    && rm -rf /tmp/tmux-*

COPY requirements.txt /tmp/requirements.txt
# Installs pytest==8.4.1 and pytest-json-ctrf==0.3.5 with hash-locked transitive deps.
RUN pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt
RUN rm -f /tmp/requirements.txt

WORKDIR /app

COPY --from=rsbuilder --chmod=0755 /build/trusteval.bin /app/bin/trusteval
COPY --from=rsbuilder --chmod=0755 /build/jarcheck.bin /app/bin/jarcheck
RUN mkdir -p /usr/lib/ceremony/bin \
    && cp /app/bin/trusteval /app/bin/jarcheck /usr/lib/ceremony/bin/ \
    && chmod 0755 /usr/lib/ceremony/bin/trusteval /usr/lib/ceremony/bin/jarcheck

COPY config/ /app/config/
COPY data/ /app/data/
COPY docs/ /app/docs/
COPY --chmod=0755 ops/run_mesh.sh /app/ops/run_mesh.sh
COPY --chmod=0755 ops/seat_uv.sh /app/ops/seat_uv.sh
COPY --chmod=0755 ops/axle_hold.sh /app/ops/axle_hold.sh
COPY --chmod=0755 ops/knit_stream.sh /app/ops/knit_stream.sh
COPY --chmod=0755 ops/fold_d.sh /app/ops/fold_d.sh
COPY --chmod=0755 ops/emit_mesh.sh /app/ops/emit_mesh.sh
COPY --chmod=0755 ops/ceremonyd_health /app/ops/ceremonyd_health
COPY ops/trust_policy.toml /app/ops/trust_policy.toml
COPY ops/matrix.toml /app/ops/matrix.toml
COPY ops/abort.d/ /app/ops/abort.d/

# Seed live ceremony trees; agent UID 65534 must write seating knobs.
RUN mkdir -p /etc/ceremony/reconcile.d \
        /var/lib/ceremony/state \
        /var/lib/ceremony/ops/abort.d \
        /output /logs/verifier /logs/agent \
    && cp /app/config/site_standard.conf /etc/ceremony/site_standard.conf \
    && cp /app/config/reconcile.d/*.conf /etc/ceremony/reconcile.d/ \
    && cp /app/ops/abort.d/90-local.conf /var/lib/ceremony/ops/abort.d/90-local.conf \
    && cp /app/ops/abort.d/90-local.conf /etc/ceremony/reconcile.d/90-local.conf \
    && printf '7\n' >/var/lib/ceremony/state/gen.target \
    && printf 'jsonl-then-wal\n' >/var/lib/ceremony/state/stream.order \
    && printf 'inclusive\n' >/var/lib/ceremony/state/hold_bound \
    && printf '%s\n' \
         'fleet_a_uv=0' \
         'fleet_a_up=0' \
         'fleet_b_uv=0' \
         'fleet_b_up=0' \
         >/var/lib/ceremony/state/uv_policy.conf \
    && : >/etc/ceremony/reconcile.conf \
    && chmod a+rw \
         /app/ops/run_mesh.sh \
         /app/ops/seat_uv.sh \
         /app/ops/axle_hold.sh \
         /app/ops/knit_stream.sh \
         /app/ops/fold_d.sh \
         /app/ops/emit_mesh.sh \
         /app/ops/ceremonyd_health \
         /app/ops/trust_policy.toml \
         /app/ops/matrix.toml \
         /app/config/site_standard.conf \
         /app/config/reconcile.d/*.conf \
    && chmod a+rwX /app/data/signed_segments \
    && chmod -R a+rwX /etc/ceremony /var/lib/ceremony /output /logs \
    && chmod 1777 /tmp \
    && rm -rf /tmp/tmux-*
