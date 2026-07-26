# syntax=docker/dockerfile:1

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

WORKDIR /build
COPY image-build /tmp/image-build
RUN chmod +x /tmp/image-build/materialize-src.sh \
    && /tmp/image-build/materialize-src.sh /build active \
    && go mod download \
    && go build -trimpath -buildvcs=false -o /out/rampd.active ./cmd/rampd \
    && /tmp/image-build/materialize-src.sh /build stale \
    && go build -trimpath -buildvcs=false -o /out/rampd.stale ./cmd/rampd

FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema \
        ca-certificates \
        tmux \
        python3 \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

RUN mkdir -p /opt/ramp/bin /opt/ramp/config /opt/ramp/scripts /opt/ramp/systemd
COPY --from=builder /out/rampd.active /opt/ramp/bin/rampd.active
COPY --from=builder /out/rampd.stale /opt/ramp/bin/rampd.stale
RUN ln -sf /opt/ramp/bin/rampd.stale /opt/ramp/bin/rampd

COPY config /opt/ramp/config
COPY systemd /opt/ramp/systemd
COPY --chmod=0755 scripts /opt/ramp/scripts
RUN /opt/ramp/scripts/build_fixtures.sh

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke

WORKDIR /opt/ramp
