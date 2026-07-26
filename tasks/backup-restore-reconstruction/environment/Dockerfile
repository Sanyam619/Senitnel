FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

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

ENV TERM=xterm-256color

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

WORKDIR /app

COPY Cargo.toml /app/Cargo.toml
COPY Cargo.lock /app/Cargo.lock
COPY src /app/src
COPY docs /app/docs
COPY config /app/config
COPY ops /app/ops
COPY bag /app/bag
COPY rim /app/rim
COPY deck /app/deck
COPY packaging /app/packaging
COPY data /app/data

# Materialise episode fixtures, pin their digests, then drop the generator.
RUN python3 /app/data/build_helpers/gen_episodes.py >/dev/null \
    && (cd /app && find data/episodes -type f | LC_ALL=C sort | xargs sha256sum) \
         >/app/packaging/episodes.sha256 \
    && rm -rf /app/data/build_helpers

# Create live admin trees and copy sealed/decoy volumes out of crash exports.
RUN mkdir -p /etc/fleet/reconcile.d /var/lib/fleet/volumes /var/lib/fleet/runtime \
        /var/lib/fleet/leases /var/lib/fleet/state /var/lib/fleet/ops/abort.d \
        /var/run/fleet/gate /var/log/fleet \
    && for ep in alpha beta gamma delta epsilon; do \
         mkdir -p "/var/lib/fleet/volumes/${ep}/sealed" \
                  "/var/lib/fleet/volumes/${ep}/decoy" \
                  "/var/lib/fleet/runtime/${ep}"; \
         cp -a "/app/data/episodes/${ep}/shelves/sealed/." \
           "/var/lib/fleet/volumes/${ep}/sealed/"; \
         if [ -d "/app/data/episodes/${ep}/shelves/decoy" ]; then \
           cp -a "/app/data/episodes/${ep}/shelves/decoy/." \
             "/var/lib/fleet/volumes/${ep}/decoy/"; \
         fi; \
       done \
    && cp /app/config/reconcile.d/*.conf /etc/fleet/reconcile.d/ \
    && cp /app/ops/journal.seed.jsonl /var/lib/fleet/ops/journal.jsonl \
    && cp /app/ops/abort.d/90-local.conf /var/lib/fleet/ops/abort.d/90-local.conf \
    && printf '7\n' >/var/lib/fleet/state/gen.target \
    && printf '3\n' >/var/lib/fleet/state/gen.live \
    && printf 'decoy\n' >/var/lib/fleet/state/attach.intent \
    && printf 'lab-tmp\n' >/var/lib/fleet/state/hold.token

# Build release bins into /app/bin at image build; keep a restore copy under /usr/lib/fleet.
RUN cargo build --release --bins \
    && mkdir -p /app/bin /usr/lib/fleet/bin \
    && cp /app/target/release/fleetctl /app/bin/fleetctl \
    && cp /app/target/release/yarder /app/bin/yarder \
    && cp /app/target/release/fleetpeek /app/bin/fleetpeek \
    && cp /app/bin/fleetctl /app/bin/yarder /app/bin/fleetpeek /usr/lib/fleet/bin/ \
    && sha256sum /app/bin/fleetpeek | awk '{print $1}' > /app/packaging/fleetpeek.sha256 \
    && chmod +x /app/ops/run_recovery.sh /app/ops/fleethealth /app/ops/fleetd \
         /app/ops/weave_k.sh /app/ops/axle_p.sh /app/ops/fold_d.sh \
         /app/bag/pull_m.sh /app/rim/mark_t.sh /app/deck/bind_v.sh \
    && rm -rf /app/target

# Baseline live admin state (pre-recovery): synonym effective policy, decoy
# runtime copies, stub leases, inverted/stale gates, abort-window holds.
RUN cp /app/config/reconcile.conf /etc/fleet/reconcile.conf \
    && cp /app/config/site_standard.conf /etc/fleet/site_standard.conf \
    && printf '%s\n' \
         '# fleetd runtime environment' \
         'PAYLOAD_LINEAGE=decoy' \
         'HOLD_TOKEN=lab-tmp' \
         'FLEET_VOLUME_ROOT=/var/lib/fleet/volumes' \
         'FLEET_RUNTIME_ROOT=/var/lib/fleet/runtime' \
         > /etc/fleet/fleetd.env \
    && for ep in alpha beta gamma delta epsilon; do \
         if [ "$ep" = "beta" ] || [ "$ep" = "epsilon" ]; then \
           printf '%s\n' \
             '{' \
             '  "slot": "borrow_primary",' \
             '  "claims": [' \
             '    {' \
             '      "peer": "atlas",' \
             '      "live": true,' \
             '      "sealed": false,' \
             '      "ts": 900,' \
             '      "token": "ops-newest"' \
             '    }' \
             '  ]' \
             '}' > "/var/lib/fleet/leases/${ep}.json"; \
         else \
           printf '%s\n' \
             '{' \
             '  "slot": "borrow_primary",' \
             '  "claims": [' \
             '    {' \
             '      "peer": "atlas",' \
             '      "live": true,' \
             '      "sealed": false,' \
             '      "ts": 50,' \
             '      "token": "ops-default"' \
             '    }' \
             '  ]' \
             '}' > "/var/lib/fleet/leases/${ep}.json"; \
         fi; \
         if [ -f "/var/lib/fleet/volumes/${ep}/decoy/payload.bin" ]; then \
           mkdir -p "/var/lib/fleet/runtime/${ep}"; \
           cp -f "/var/lib/fleet/volumes/${ep}/decoy/payload.bin" \
             "/var/lib/fleet/runtime/${ep}/payload.bin"; \
         else \
           mkdir -p "/var/lib/fleet/runtime/${ep}"; \
           cp -f "/var/lib/fleet/volumes/${ep}/sealed/payload.bin" \
             "/var/lib/fleet/runtime/${ep}/payload.bin"; \
         fi; \
         printf 'lab-tmp\n' >"/var/lib/fleet/runtime/${ep}/.hold"; \
       done \
    && mkdir -p /var/run/fleet/gate/epsilon /var/run/fleet/gate/beta /var/run/fleet/gate/alpha \
    && touch /var/run/fleet/gate/epsilon/cinder /var/run/fleet/gate/epsilon/mesa \
             /var/run/fleet/gate/beta/ridge /var/run/fleet/gate/alpha/mesa \
    && rm -f /var/run/fleet/fleetd.pid /var/run/fleet/fleetd.heartbeat

ENV PATH="/app/bin:${PATH}"
WORKDIR /app
