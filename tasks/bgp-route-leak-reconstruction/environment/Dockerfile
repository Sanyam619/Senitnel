# syntax=docker/dockerfile:1

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY cmd/ ./cmd/
COPY internal/ ./internal/
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/converge ./cmd/converge \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/audit ./cmd/audit

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Agent runtime requires tmux and asciinema before any other setup.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        tmux=3.3a-3 \
        bash \
        ca-certificates \
        procps \
        python3 \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color

RUN tmux -V && asciinema --version

COPY requirements.txt /tmp/requirements.txt
# Installs pytest==8.4.1 and pytest-json-ctrf==0.3.5 with hash-locked transitive deps.
RUN python3 -m pip install --no-cache-dir --break-system-packages --require-hashes \
    -r /tmp/requirements.txt
RUN rm -f /tmp/requirements.txt

ENV GOPATH=/go \
    GOCACHE=/tmp/go-cache
RUN mkdir -p /go /tmp/go-cache

COPY go.mod go.sum /opt/bgplab/
RUN cd /opt/bgplab && go mod download

COPY --from=builder --chmod=755 /out/converge /opt/bgplab/bin/converge
COPY --from=builder --chmod=755 /out/audit /opt/bgplab/bin/audit
COPY cmd/ /opt/bgplab/cmd/
COPY internal/ /opt/bgplab/internal/
COPY data/ /opt/bgplab/data/
COPY docs/ /opt/bgplab/docs/

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

WORKDIR /opt/bgplab
ENV PATH="/opt/bgplab/bin:${PATH}"
