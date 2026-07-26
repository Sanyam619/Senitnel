# syntax=docker/dockerfile:1
#
# Single-stage: Rust builds correct prebuilt bops/healthb; broken ops are
# bash helpers under wire/rim/ops/bag/deck/dock writing live /etc + /var.

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.title="btrfs-send-parent-qgroup-cutover"
LABEL org.opencontainers.image.version="1.1.0"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        bash \
        ca-certificates \
        coreutils \
        python3 \
        python3-pip \
        python-is-python3 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

RUN install -d -m 1777 /tmp \
    && install -d -m 0777 /tmp/.config /tmp/.config/asciinema \
    && tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

ENV HOME=/tmp
ENV TMUX_TMPDIR=/tmp
ENV TERM=xterm-256color
ENV XDG_CONFIG_HOME=/tmp/.config
ENV PATH="/app/bin:/app/ops:${PATH}"
ENV BTRFS_ROOT=/var/lib/btrfs
ENV BTRFS_SEAL=/etc/btrfs/pool.seal
ENV LANE_ROSTER=/etc/btrfs/lane.roster
ENV BTRFS_PREF_D=/etc/btrfs/pref.d
ENV LEASE_DIR=/var/run/btrfs
ENV BTRFS_JOURNAL=/var/lib/btrfs/ops/journal.jsonl
ENV BTRFS_DESKD_ENV=/etc/btrfs/deskd.env

COPY Cargo.toml Cargo.lock ./
COPY src ./src
COPY docs/ /app/docs/
COPY packaging/ /app/packaging/
COPY config/ /app/config/
COPY --chmod=755 ops/ /app/ops/
COPY --chmod=755 wire/ /app/wire/
COPY --chmod=755 rim/ /app/rim/
COPY --chmod=755 bag/ /app/bag/
COPY --chmod=755 deck/ /app/deck/
COPY --chmod=755 dock/ /app/dock/
COPY etc/btrfs/ /etc/btrfs/
COPY data/ /app/data/

RUN python3 /app/data/build_fixtures.py \
    && mkdir -p /var/lib/btrfs /var/run/btrfs /var/log/btrfs /output/lanes \
    && cp -a /app/data/btrfs/. /var/lib/btrfs/ \
    && printf '1\n' >/var/lib/btrfs/meta/gen.target \
    && cargo build --release --locked --bins \
    && mkdir -p /app/bin /usr/lib/btrfs/bin \
    && cp target/release/bops target/release/healthb /app/bin/ \
    && cp /app/bin/bops /app/bin/healthb /usr/lib/btrfs/bin/ \
    && chmod 755 /app/ops/*.sh /app/ops/deskd /app/ops/run_cutover.sh \
         /app/wire/*.sh /app/rim/*.sh /app/bag/*.sh /app/deck/*.sh /app/dock/*.sh \
    && rm -rf /app/target /app/data/build_fixtures.py \
    && rm -f /app/Cargo.toml /app/Cargo.lock \
    && rm -rf /app/src
