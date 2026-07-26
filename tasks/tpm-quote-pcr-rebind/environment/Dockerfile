# syntax=docker/dockerfile:1

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

WORKDIR /build

COPY go.mod go.sum ./
RUN go mod download

COPY cmd/ ./cmd/
COPY internal/ ./internal/
COPY pkg/ ./pkg/

RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/benchcheck ./cmd/benchcheck \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/floorcheck ./cmd/floorcheck \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/fwreplay ./cmd/fwreplay \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/logscan ./cmd/logscan \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/sealmake ./cmd/sealmake \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/blobhash ./cmd/blobhash

FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

# Agent runtime requires tmux and asciinema before COPY layers below.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema \
        tmux \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates=20230311+deb12u1 \
        coreutils=9.1-1 \
        openssl=3.0.17-1~deb12u2 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY --from=builder --chmod=755 \
    /out/benchcheck /out/floorcheck /out/fwreplay /out/logscan /out/sealmake /out/blobhash \
    /opt/rly/bin/
COPY config/ /opt/rly/config/
COPY --chmod=755 scripts/ /opt/rly/scripts/
COPY cmd/ /opt/rly/src/cmd/
COPY internal/ /opt/rly/src/internal/
COPY pkg/ /opt/rly/src/pkg/
COPY go.mod go.sum /opt/rly/src/
COPY data/build_fixtures.sh /tmp/build_fixtures.sh

RUN chmod +x /tmp/build_fixtures.sh \
    && /tmp/build_fixtures.sh \
    && rm /tmp/build_fixtures.sh

RUN ln -sf /opt/rly/config /data/config

WORKDIR /data
