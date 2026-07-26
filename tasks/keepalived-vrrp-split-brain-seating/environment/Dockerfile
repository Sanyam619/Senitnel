# syntax=docker/dockerfile:1
# Canonical sysadmin runtime base (Dockerfile & Image Best Practices §2 /
# docker environment.mdc — System Administration Task).
FROM public.ecr.aws/docker/library/ubuntu:24.04@sha256:0d39fcc8335d6d74d5502f6df2d30119ff4790ebbb60b364818d5112d9e3e932

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.title="keepalived-vrrp-split-brain-seating"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

ENV DEBIAN_FRONTEND=noninteractive \
    HOME=/tmp \
    TMUX_TMPDIR=/tmp \
    TERM=xterm-256color \
    XDG_CONFIG_HOME=/tmp/.config \
    PATH="/app/publisher:/app/ops:/app/cli:${PATH}" \
    KV_ETC=/etc/keepalived \
    KV_OPS=/var/lib/keepalived/ops \
    KV_REPORT=/output/vrrp-seat.json

WORKDIR /app

# 1. OS packages (least volatile) — pinned; tmux + asciinema required for agent runtime.
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

# 2. Verifier Python deps (hashed lockfile; separate RUN from apt and from rm).
COPY requirements.txt /tmp/requirements.txt
# Installs pytest==8.4.1 and pytest-json-ctrf==0.3.5 with hash-locked transitive deps.
RUN python3 -m pip install --no-cache-dir --break-system-packages --require-hashes \
    -r /tmp/requirements.txt
RUN rm -f /tmp/requirements.txt

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

# 3. Task materials (more volatile) — narrow COPY, not COPY .
COPY docs/ /app/docs/
COPY packaging/ /app/packaging/
COPY config/ /app/config/
COPY data/ /app/data/
COPY seed/ /app/seed/
COPY --chmod=755 ops/ /app/ops/
COPY --chmod=755 publisher/ /app/publisher/
COPY --chmod=755 cli/ /app/cli/

# 4. Materialize live desk + surface CLI (no solution/tests in image).
RUN mkdir -p /output \
        /etc/keepalived/conf.d /etc/keepalived/runtime \
        /var/lib/keepalived/ops/holds /var/lib/keepalived/ops/floors \
        /var/lib/keepalived/ops/state /var/lib/keepalived/ops/abort.d \
        /var/lib/keepalived/ops/live /var/lib/keepalived/ops/track \
        /var/lib/keepalived/ops/netif /var/log/keepalived \
    && cp -a /app/seed/etc/keepalived/. /etc/keepalived/ \
    && cp -a /app/seed/var/lib/keepalived/ops/. /var/lib/keepalived/ops/ \
    && cp -a /app/cli/. /usr/local/bin/ \
    && ln -sf /app/publisher/vrrpseat /usr/local/bin/vrrpseat \
    && (cd /app/data/vrrp && sha256sum ./*.conf | LC_ALL=C sort) > /app/packaging/vrrp.sha256 \
    && sha256sum /app/publisher/vrrpseat | awk '{print $1"  /app/publisher/vrrpseat"}' >> /app/packaging/vrrp.sha256 \
    && chmod 755 /app/ops/*.sh /app/publisher/* /usr/local/bin/vrrphealth /usr/local/bin/seatview \
    && printf '%s\n' 'peer_a MASTER' 'peer_b MASTER' 'peer_e MASTER' \
         > /etc/keepalived/runtime/token.map \
    && rm -rf /app/seed
