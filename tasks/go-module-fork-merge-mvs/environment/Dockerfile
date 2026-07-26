# syntax=docker/dockerfile:1

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS mxbuilder

WORKDIR /build/matrixci
COPY matrixci/go.mod ./
RUN go mod download
COPY matrixci/cmd/ cmd/
COPY matrixci/internal/ internal/
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/matrixci ./cmd/matrixci

FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema \
        ca-certificates \
        procps \
        tmux \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux send-keys -t _smoke 'echo tmux_ok' Enter \
    && tmux capture-pane -t _smoke -p | grep -q tmux_ok \
    && tmux kill-session -t _smoke

RUN pip install --no-cache-dir \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY --from=mxbuilder --chmod=755 /out/matrixci /app/bin/matrixci

COPY proxy/ /app/proxy/
COPY src/ /app/src/
COPY docs/ /app/docs/

RUN mkdir -p /output

ENV PATH="/app/bin:${PATH}"

WORKDIR /app
