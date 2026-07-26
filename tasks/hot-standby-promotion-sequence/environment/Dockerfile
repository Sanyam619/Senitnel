# syntax=docker/dockerfile:1

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

WORKDIR /build

COPY go.mod ./
RUN go mod download

COPY cmd/ ./cmd/
COPY internal/ ./internal/
COPY pkg/ ./pkg/

RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/vlogscan ./cmd/vlogscan \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/shmbind ./cmd/shmbind \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/sqlexport ./cmd/sqlexport \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/pairwatch ./cmd/pairwatch \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/logpack ./cmd/logpack

FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

# Agent runtime requires tmux and asciinema before any other setup.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates=20230311+deb12u1 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        sqlite3=3.40.1-2+deb12u2 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY --from=builder /out/vlogscan /out/shmbind /out/sqlexport /out/pairwatch /out/logpack /opt/lab/bin/
COPY config/lab.toml /opt/lab/config/lab.toml
COPY scripts/ /opt/lab/scripts/
COPY libexec/ /opt/lab/libexec/
COPY libexec/ /app/libexec/
COPY scripts/ /app/scripts/
COPY data/build_fixtures.sh /tmp/build_fixtures.sh

RUN chmod +x /opt/lab/bin/* /opt/lab/scripts/*.sh /opt/lab/libexec/promote/*.sh /tmp/build_fixtures.sh \
    && /tmp/build_fixtures.sh \
    && rm /tmp/build_fixtures.sh

WORKDIR /data
