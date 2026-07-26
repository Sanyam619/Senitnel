# syntax=docker/dockerfile:1
# Canonical sysadmin runtime base (Dockerfile & Image Best Practices §2 /
# docker environment.mdc — System Administration Task).
FROM public.ecr.aws/docker/library/ubuntu:24.04@sha256:0d39fcc8335d6d74d5502f6df2d30119ff4790ebbb60b364818d5112d9e3e932

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.title="squid-cache-peer-icp-preference-lattice"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

ENV DEBIAN_FRONTEND=noninteractive \
    HOME=/tmp \
    TMUX_TMPDIR=/tmp \
    TERM=xterm-256color \
    XDG_CONFIG_HOME=/tmp/.config \
    PATH="/app/bin:/app/ops:${PATH}" \
    SQ_ETC=/etc/squid \
    SQ_VAR=/var/lib/squid \
    SQ_RUN=/var/run/squid \
    SQ_REPORT=/output/squid-seat.json

WORKDIR /app

# 1. OS packages (least volatile) — pinned; tmux + asciinema required for agent runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.4.0-1 \
        bash=5.2.21-2ubuntu4 \
        ca-certificates=20260601~24.04.1 \
        coreutils=9.4-3ubuntu6.2 \
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
COPY --chmod=755 ops/ /app/ops/
COPY --chmod=755 rim/ /app/rim/
COPY --chmod=755 bag/ /app/bag/
COPY --chmod=755 deck/ /app/deck/
COPY --chmod=755 wire/ /app/wire/
COPY --chmod=755 tools/ /app/tools/

# 4. Materialize live desk + install surface health symlink (no solution/tests in image).
RUN mkdir -p /app/bin \
    && cp -a /app/tools/squidhealth /app/tools/sockprobe /app/bin/ \
    && chmod 755 /app/bin/squidhealth /app/bin/sockprobe \
    && bash /app/data/build_fixtures.sh \
    && install -d -m 0755 /output /var/log/squid \
    && ln -sf /app/bin/squidhealth /usr/local/bin/squidhealth \
    && chmod 755 /app/ops/*.sh /app/rim/*.sh /app/bag/*.sh /app/deck/*.sh /app/wire/*.sh \
         /app/ops/run_squid_seat.sh \
    && rm -f /app/data/build_fixtures.sh
