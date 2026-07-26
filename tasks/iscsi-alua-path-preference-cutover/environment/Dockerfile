# syntax=docker/dockerfile:1
#
# iSCSI/ALUA multipath seating desk. Broken ops write live /etc + /var; the
# surface status helper may print ready while seating truth is wrong.

FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.title="iscsi-alua-path-preference-cutover"
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
COPY --chmod=755 tools/mpathhealth /usr/local/bin/mpathhealth
COPY config/ /app/config/

# Materialize live /etc + /var from config seeds (broken baseline).
RUN mkdir -p \
        /etc/multipath/conf.d \
        /var/lib/multipath/ops \
        /var/lib/multipath/candidates \
        /output \
        /logs/verifier \
    && cp /app/config/multipath/multipath.conf /etc/multipath/multipath.conf \
    && cp -a /app/config/multipath/conf.d/. /etc/multipath/conf.d/ \
    && cp /app/config/authority.toml /var/lib/multipath/ops/authority.toml \
    && cp /app/config/roster.toml /var/lib/multipath/ops/roster.toml \
    && cp /app/config/holds.toml /var/lib/multipath/ops/holds.toml \
    && cp /app/config/prefer.surface.toml /var/lib/multipath/ops/prefer.toml \
    && chmod 755 /app/ops/*.sh /app/rim/*.sh /app/decoy/*.sh /usr/local/bin/mpathhealth

WORKDIR /app
