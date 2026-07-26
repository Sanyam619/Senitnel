# syntax=docker/dockerfile:1
FROM public.ecr.aws/docker/library/ubuntu:24.04@sha256:0d39fcc8335d6d74d5502f6df2d30119ff4790ebbb60b364818d5112d9e3e932

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.title="systemd-path-unit-watch-seating"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

ENV DEBIAN_FRONTEND=noninteractive \
    HOME=/tmp \
    TMUX_TMPDIR=/tmp \
    TERM=xterm-256color \
    XDG_CONFIG_HOME=/tmp/.config \
    PATH="/app/publisher:/app/ops:/app/cli:${PATH}" \
    SYS_ETC=/etc/systemd/system \
    SYS_OPS=/var/lib/systemd/ops \
    SEAT_REPORT=/output/path-seat.json

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.4.0-1 \
        bash=5.2.21-2ubuntu4 \
        ca-certificates=20260601~24.04.1 \
        coreutils=9.4-3ubuntu6.2 \
        jq=1.7.1-3ubuntu0.24.04.2 \
        python-is-python3=3.11.4-1 \
        python3=3.12.3-0ubuntu2.1 \
        python3-pip=24.0+dfsg-1ubuntu1.3 \
        tmux=3.4-1ubuntu0.1 \
        util-linux=2.39.3-9ubuntu6.4 \
    && rm -rf /var/lib/apt/lists/*

# Verifier Python deps (hashed lockfile; pytest and pytest-json-ctrf).
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --no-cache-dir --break-system-packages --require-hashes \
    -r /tmp/requirements.txt
RUN rm -f /tmp/requirements.txt

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

# Task materials (narrow COPY, not COPY .).
COPY docs/ /app/docs/
COPY packaging/ /app/packaging/
COPY config/ /app/config/
COPY data/ /app/data/
COPY seed/ /app/seed/
COPY --chmod=755 ops/ /app/ops/
COPY --chmod=755 publisher/ /app/publisher/
COPY --chmod=755 cli/ /app/cli/

# Materialize the live desk + surface CLI (no solution/tests in image).
RUN mkdir -p /output \
        /etc/systemd/system \
        /var/lib/systemd/ops/floors /var/lib/systemd/ops/watchgen \
        /var/lib/systemd/ops/state /var/lib/systemd/ops/abort.d \
        /var/lib/systemd/ops/live /run/systemd/watch-seat \
        /var/run/systemd-seat /var/log/watch-seat \
    && cp -a /app/seed/etc/systemd/system/. /etc/systemd/system/ \
    && cp -a /app/seed/var/lib/systemd/ops/. /var/lib/systemd/ops/ \
    && cp -a /app/cli/. /usr/local/bin/ \
    && ln -sf /app/publisher/pathseat /usr/local/bin/pathseat \
    && (cd /app/data/pathunits && sha256sum ./*.meta | LC_ALL=C sort) > /app/packaging/pathunits.sha256 \
    && sha256sum /app/publisher/pathseat | awk '{print $1"  /app/publisher/pathseat"}' >> /app/packaging/pathunits.sha256 \
    && chmod 755 /app/ops/*.sh /app/publisher/* /usr/local/bin/pathhealth /usr/local/bin/seatpeek \
    && printf '%s\n' 'deploy-artifact ARMED' 'config-reload ARMED' 'spool-flush ARMED' \
         > /run/systemd/watch-seat/loaded.map \
    && rm -rf /app/seed
