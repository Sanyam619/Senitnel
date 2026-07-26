# syntax=docker/dockerfile:1
#
# Lab Samba idmap cutover. Sealed tipfold/cutarm/idmapctl; broken ops bash
# writes live /etc + /var. Opaque tips.bin/journal.bin; plaintext JSONL decoys.

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

WORKDIR /build
COPY go.mod ./
COPY src/ ./src/
COPY decoy/ ./decoy/
RUN mkdir -p /out/bin \
    && go build -trimpath -ldflags="-s -w" -o /out/bin/idmapctl ./src/idmapctl \
    && go build -trimpath -ldflags="-s -w" -o /out/bin/tipfold ./src/tipfold \
    && go build -trimpath -ldflags="-s -w" -o /out/bin/cutarm ./src/cutarm \
    && go build -trimpath -ldflags="-s -w" -o /out/bin/tipcheck ./src/tipcheck \
    && go build -trimpath -ldflags="-s -w" -o /out/bin/jrnlcheck ./src/jrnlcheck \
    && go build -trimpath -ldflags="-s -w" -o /out/bin/scan_fold ./decoy/scan_fold.go \
    && gcc -O2 -Wall -o /out/bin/bind_probe decoy/bind_probe.c

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.title="samba-winbind-idmap-cutover"
LABEL org.opencontainers.image.version="4.0.0"
LABEL org.opencontainers.image.licenses="MIT"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        tmux=3.3a-3 \
        ca-certificates=20230311+deb12u1 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
    && rm -rf /var/lib/apt/lists/*

RUN install -d -m 1777 /tmp \
    && install -d -m 0777 /tmp/.config /tmp/.config/asciinema \
    && test -x /usr/bin/tmux \
    && test -x /usr/bin/asciinema \
    && tmux -V \
    && asciinema --version

ENV HOME=/tmp
ENV TMUX_TMPDIR=/tmp
ENV TERM=xterm-256color
ENV XDG_CONFIG_HOME=/tmp/.config
ENV PATH="/app/bin:/app/ops:${PATH}"
ENV SAMBA_ETC=/etc/samba
ENV SAMBA_VAR=/var/lib/samba
ENV IDMAP_ROSTER=/etc/samba/idmap.roster
ENV IDMAP_TDB=/var/lib/samba/idmap.tdb
ENV DESK_SEAL=/etc/samba/desk.seal
ENV IDMAP_REPORT=/output/idmap-cutover.json
ENV PREF_D=/etc/samba/pref.d
ENV SAMBA_DESKD_ENV=/etc/samba/deskd.env

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY --from=builder --chmod=755 \
    /out/bin/idmapctl /out/bin/tipfold /out/bin/cutarm \
    /out/bin/tipcheck /out/bin/jrnlcheck \
    /out/bin/scan_fold /out/bin/bind_probe \
    /app/bin/
RUN mkdir -p /usr/lib/samba/bin \
    && cp -a /app/bin/idmapctl /app/bin/tipfold /app/bin/cutarm /usr/lib/samba/bin/

COPY --chmod=755 tools/wbinfo tools/smblist /app/bin/
COPY --chmod=755 ops/ /app/ops/
COPY --chmod=755 wire/ /app/wire/
COPY --chmod=755 rim/ /app/rim/
COPY --chmod=755 bag/ /app/bag/
COPY --chmod=755 deck/ /app/deck/
COPY --chmod=755 dock/ /app/dock/
COPY decoy/ /app/decoy/
COPY docs/ /app/docs/
COPY config/ /app/config/
COPY data/fixtures/ /app/data/fixtures/
COPY samba-seed/ /app/samba-seed/
COPY --chmod=755 scripts/materialize_lab.sh scripts/pack_opaque.py /app/scripts/

RUN printf '#!/bin/bash\nexit 0\n' >/app/bag/noop.sh && chmod 755 /app/bag/noop.sh

RUN /app/scripts/materialize_lab.sh /app/samba-seed \
    && mkdir -p /output \
    && chmod 755 /app/ops/* /app/wire/* /app/rim/* /app/deck/* /app/dock/* \
         /app/bin/* \
    && rm -rf /app/samba-seed/journal /app/samba-seed/ops/journal.jsonl 2>/dev/null || true

WORKDIR /app
