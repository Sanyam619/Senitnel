# syntax=docker/dockerfile:1
#
# Chrony/timesync seating desk. Broken ops write live /etc + /var; surface
# timehealth may look synchronized while seating truth is wrong.

FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.title="chrony-stratum-preference-lattice"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        bash \
        ca-certificates=20230311+deb12u1 \
        coreutils \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        python-is-python3 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

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

ENV HOME=/tmp
ENV TMUX_TMPDIR=/tmp
ENV TERM=xterm-256color
ENV XDG_CONFIG_HOME=/tmp/.config
ENV PATH="/app/ops:/usr/local/bin:${PATH}"

COPY docs/ /app/docs/
COPY packaging/ /app/packaging/
COPY data/ /app/data/
COPY --chmod=755 ops/ /app/ops/
COPY --chmod=755 rim/ /app/rim/
COPY --chmod=755 decoy/ /app/decoy/
COPY --chmod=755 tools/timehealth /usr/local/bin/timehealth
COPY config/ /app/config/

# Materialize live /etc + /var from config seeds (broken baseline).
RUN mkdir -p \
        /etc/chrony/sources.d \
        /etc/systemd/timesyncd.conf.d \
        /var/lib/chrony \
        /var/lib/time/ops \
        /var/lib/time/surface/sources.d \
        /var/lib/time/surface/timesync.d \
        /output \
        /logs/verifier \
    && cp /app/config/chrony/chrony.conf /etc/chrony/chrony.conf \
    && cp -a /app/config/chrony/sources.d/. /etc/chrony/sources.d/ \
    && cp -a /app/config/timesync.d/. /etc/systemd/timesyncd.conf.d/ \
    && cp -a /app/config/surface/sources.d/. /var/lib/time/surface/sources.d/ \
    && cp -a /app/config/surface/timesync.d/. /var/lib/time/surface/timesync.d/ \
    && cp /app/config/prefer.surface.toml /var/lib/time/ops/prefer.toml \
    && cp /app/config/authority.toml /var/lib/time/ops/authority.toml \
    && cp /app/config/roster.toml /var/lib/time/ops/roster.toml \
    && cp /app/config/holds.toml /var/lib/time/ops/holds.toml \
    && cp /app/config/offsets.toml /var/lib/time/ops/offsets.toml \
    && cp /app/config/holds.toml /var/lib/chrony/holds.toml \
    && printf '0.0\n' > /var/lib/chrony/drift \
    && chmod 755 /app/ops/*.sh /app/rim/*.sh /app/decoy/*.sh /usr/local/bin/timehealth

WORKDIR /app
