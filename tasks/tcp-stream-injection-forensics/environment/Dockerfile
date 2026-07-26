# syntax=docker/dockerfile:1

# TB3 canonical runtime base: debian:bookworm-slim (pinned below).
# Builder stage uses golang:1.24-bookworm because no Go image is listed
# in the TB3 canonical base set yet; this task ships a prebuilt wiretap
# binary and leaves the full module tree for agent-side rebuilds.

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY cmd/ ./cmd/
COPY internal/ ./internal/
COPY pkg/ ./pkg/
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/wiretap ./cmd/wiretap

FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Agent session stack (tmux, asciinema) plus verifier runtime in one apt transaction.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
        bash \
        ca-certificates \
        coreutils \
        procps \
        python3 \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

ENV TERM=xterm-256color

COPY --from=builder /usr/local/go /usr/local/go
ENV PATH="/usr/local/go/bin:/opt/wiretap/bin:${PATH}" \
    GOPATH=/go \
    GOCACHE=/tmp/go-cache
RUN mkdir -p /go /tmp/go-cache
COPY --from=builder --chmod=755 /out/wiretap /opt/wiretap/bin/wiretap
COPY cmd/ /opt/wiretap/cmd/
COPY internal/ /opt/wiretap/internal/
COPY pkg/ /opt/wiretap/pkg/
COPY config/ /opt/wiretap/config/
COPY go.mod go.sum /opt/wiretap/
COPY data/manifest.json /opt/wiretap/data/manifest.json
COPY data/build_captures.py /tmp/build_captures.py
RUN mkdir -p /opt/wiretap/data/captures \
    && CAPTURE_OUT=/opt/wiretap/data/captures python3 /tmp/build_captures.py \
    && rm /tmp/build_captures.py

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

WORKDIR /opt/wiretap
