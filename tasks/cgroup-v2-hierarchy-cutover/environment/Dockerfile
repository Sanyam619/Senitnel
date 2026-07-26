# syntax=docker/dockerfile:1

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

WORKDIR /build

COPY go.mod go.sum ./
RUN go mod download

COPY cmd/ ./cmd/
COPY internal/ ./internal/
COPY pkg/ ./pkg/

RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/topscan ./cmd/surfcheck \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/treewalk ./cmd/nodescope \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/slicearm ./cmd/phasegate \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/benchunit ./cmd/loadpulse \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/ledgersnap ./cmd/acctpull \
    && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/shadowlift ./cmd/shadowlift

FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

# Agent runtime requires tmux and asciinema before COPY layers below.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        tmux=3.3a-3 \
        ca-certificates=20230311+deb12u1 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY --from=builder /usr/local/go /usr/local/go
ENV PATH="/usr/local/go/bin:${PATH}"

COPY --from=builder --chmod=755 \
    /out/topscan /out/treewalk /out/slicearm /out/benchunit /out/ledgersnap /out/shadowlift \
    /opt/lab/bin/
COPY config/ /opt/lab/config/
COPY --chmod=755 scripts/ /opt/lab/scripts/
COPY data/build_fixtures.sh /tmp/build_fixtures.sh

COPY go.mod go.sum /opt/lab/src/
COPY cmd/ /opt/lab/src/cmd/
COPY internal/ /opt/lab/src/internal/
COPY pkg/ /opt/lab/src/pkg/

RUN chmod +x /tmp/build_fixtures.sh \
    && /tmp/build_fixtures.sh \
    && rm /tmp/build_fixtures.sh

WORKDIR /data
