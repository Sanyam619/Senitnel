# syntax=docker/dockerfile:1

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

WORKDIR /build
COPY go.mod ./
RUN go mod download
COPY cmd/ ./cmd/
COPY internal/ ./internal/
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/reconcile ./cmd/reconcile

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Agent runtime requires tmux and asciinema before any other setup.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux=3.3a-3 \
        asciinema=2.2.0-1 \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color

RUN tmux -V && asciinema --version

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        libutempter0 \
        procps \
        python3 \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

ENV GOPATH=/go \
    GOCACHE=/tmp/go-cache
RUN mkdir -p /go /tmp/go-cache

COPY --from=builder --chmod=755 /out/reconcile /opt/wghandoff/bin/reconcile
COPY go.mod /opt/wghandoff/
COPY cmd/ /opt/wghandoff/cmd/
COPY internal/ /opt/wghandoff/internal/
COPY scripts/ /opt/wghandoff/scripts/
COPY data/ /opt/wghandoff/data/
COPY config/ /opt/wghandoff/config/
COPY docs/ /opt/wghandoff/docs/

RUN chmod +x /opt/wghandoff/scripts/*.sh \
    && cd /opt/wghandoff && go mod download

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux send-keys -t _smoke 'echo tmux_ok' Enter \
    && tmux capture-pane -t _smoke -p | grep -q tmux_ok \
    && tmux kill-session -t _smoke

WORKDIR /opt/wghandoff
ENV PATH="/opt/wghandoff/bin:${PATH}"
