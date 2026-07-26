# syntax=docker/dockerfile:1

# Builder: compile the CSP binary.
FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY cmd ./cmd
COPY anchor ./anchor
COPY propagate ./propagate
COPY gate ./gate
COPY internal ./internal
RUN go build -trimpath -buildvcs=false -o /build/cspd ./cmd/cspd

# Runtime: canonical Go image (agent rebuild + verifier session tools).
FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema \
        bash \
        ca-certificates \
        procps \
        python3 \
        python3-pip \
        tmux \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

ENV TERM=xterm-256color \
    GOPATH=/go \
    GOCACHE=/tmp/go-cache
RUN mkdir -p /go /tmp/go-cache

COPY --from=builder /build/cspd /opt/csp/bin/cspd
COPY go.mod go.sum /opt/csp/
COPY cmd /opt/csp/cmd
COPY anchor /opt/csp/anchor
COPY propagate /opt/csp/propagate
COPY gate /opt/csp/gate
COPY internal /opt/csp/internal
COPY config /opt/csp/config
COPY --chmod=0755 scripts /opt/csp/scripts
RUN /opt/csp/scripts/build_fixtures.sh

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

WORKDIR /opt/csp
