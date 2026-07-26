# syntax=docker/dockerfile:1

# Builder — canonical Go family image (dockerfile and image best practices §2).
# gcc/libc headers ship in this image; CGO builds the native force kernel.
FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

WORKDIR /build
COPY go.mod ./
RUN go mod download
COPY cmd/ ./cmd/
COPY internal/ ./internal/
COPY native/ ./native/
ENV CGO_ENABLED=1
RUN go build -trimpath -ldflags="-s -w" -o /out/campaign ./cmd/campaign

# Runtime — same canonical Go image so agents can rebuild after source edits
# (CGO toolchain already present; no second apt stage for build tools).
FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# Single apt transaction: agent session tools + verifier Python only.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        bash \
        ca-certificates=20230311+deb12u1 \
        libutempter0 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color \
    GOPATH=/go \
    GOCACHE=/tmp/go-cache \
    CGO_ENABLED=1 \
    NBODY_ROOT=/app \
    PATH="/app/bin:${PATH}"

RUN tmux -V && asciinema --version

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

RUN mkdir -p /go /tmp/go-cache /app/bin /output

# Prebuilt campaign binary at /app/bin/campaign. Agent-facing
# /app/scripts/run_campaign.sh rebuilds from /app sources before running.
COPY --from=builder --chmod=755 /out/campaign /app/bin/campaign
COPY go.mod /app/
COPY cmd/ /app/cmd/
COPY internal/ /app/internal/
COPY native/ /app/native/
COPY scripts/ /app/scripts/
COPY data/ /app/data/
COPY config/ /app/config/
COPY docs/ /app/docs/

RUN chmod +x /app/scripts/*.sh \
    && cd /app && go mod download \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux send-keys -t _smoke 'echo tmux_ok' Enter \
    && tmux capture-pane -t _smoke -p | grep -q tmux_ok \
    && tmux kill-session -t _smoke

WORKDIR /app
