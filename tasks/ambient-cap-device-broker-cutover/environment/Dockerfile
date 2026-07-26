# syntax=docker/dockerfile:1

FROM public.ecr.aws/docker/library/gcc:13-bookworm@sha256:930f2ebe239275fa67226654cb79273ea34eee672ae61c8a39f689c37fb7ac5c AS builder

WORKDIR /build
COPY Makefile ./
COPY include/ ./include/
COPY lib/ ./lib/
COPY lane/ ./lane/
COPY seat/ ./seat/
COPY roll/ ./roll/
COPY cmd/ ./cmd/
RUN make

FROM public.ecr.aws/docker/library/gcc:13-bookworm@sha256:930f2ebe239275fa67226654cb79273ea34eee672ae61c8a39f689c37fb7ac5c

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.title="ambient-cap-device-broker-cutover"
LABEL org.opencontainers.image.version="1.0.0"
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
    && command -v gcc \
    && command -v make

ENV HOME=/tmp
ENV TMUX_TMPDIR=/tmp
ENV TERM=xterm-256color
ENV XDG_CONFIG_HOME=/tmp/.config
ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

RUN mkdir -p /opt/broker/bin /opt/broker/units /opt/broker/config /output /data

COPY --from=builder --chmod=755 \
    /build/bin/topsurf /build/bin/nsprobe /build/bin/laneapply \
    /build/bin/nodeseat /build/bin/racepulse /build/bin/ledgerout \
    /opt/broker/bin/

WORKDIR /app

COPY Makefile /app/Makefile
COPY include/ /app/include/
COPY lib/ /app/lib/
COPY lane/ /app/lane/
COPY seat/ /app/seat/
COPY roll/ /app/roll/
COPY cmd/ /app/cmd/
COPY units/ /app/units/
COPY config/ /app/config/
COPY --chmod=755 scripts/ /opt/broker/scripts/
COPY --chmod=755 data/build_fixtures.sh /tmp/build_fixtures.sh

RUN /tmp/build_fixtures.sh \
    && rm /tmp/build_fixtures.sh \
    && chmod +x /opt/broker/scripts/*.sh

WORKDIR /app
