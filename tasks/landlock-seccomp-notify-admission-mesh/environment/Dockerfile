# syntax=docker/dockerfile:1
FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

LABEL org.opencontainers.image.version="1.0.0"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema \
        tmux \
        ca-certificates \
        python3 \
        python3-pip \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color \
    LANG=C.UTF-8 \
    GOPROXY=off \
    GOFLAGS="-mod=mod" \
    PATH="/usr/local/go/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

RUN command -v tmux \
    && command -v asciinema \
    && tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke \
    && command -v go \
    && go version \
    && command -v gcc

COPY requirements.txt /tmp/requirements.txt
# Installs pytest==8.4.1 and pytest-json-ctrf==0.3.5 with hash-locked transitive deps.
RUN python3 -m pip install --no-cache-dir --break-system-packages --require-hashes \
    -r /tmp/requirements.txt
RUN rm -f /tmp/requirements.txt

WORKDIR /app

COPY Makefile /app/Makefile
COPY qx/go.mod qx/go.sum /app/qx/
COPY include /app/include
COPY rz /app/rz
COPY qx/cmd /app/qx/cmd
COPY qx/internal /app/qx/internal
COPY --chmod=0755 scripts/ /app/scripts/
COPY docs /app/docs
COPY config /app/config
COPY data /app/data
COPY ops /app/ops

COPY tools/framecheck /tmp/framecheck
RUN mkdir -p /app/bin /output \
    && cd /tmp/framecheck \
    && go build -o /app/bin/framecheck . \
    && rm -rf /tmp/framecheck \
    && cd /app \
    && make \
    && test -x /app/bin/meshctl \
    && test -x /app/bin/nhelper \
    && test -x /app/bin/surfcheck \
    && test -x /app/bin/framecheck \
    && test ! -d /app/tools

WORKDIR /app
