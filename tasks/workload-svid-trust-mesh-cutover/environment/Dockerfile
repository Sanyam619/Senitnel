# Dual-language runtime: canonical Go final stage + JDK from canonical Temurin.
# Dockerfile & Image Best Practices §2 (sanctioned bases) and §4 (layer order).
#
# Final runtime base (checked by CI):
#   public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac
# JDK copied from:
#   public.ecr.aws/docker/library/eclipse-temurin:21-jdk-jammy@sha256:25d1276565738d3c805e632a4542c3a7598866ef967f4def6544c15de3a74b14

FROM public.ecr.aws/docker/library/eclipse-temurin:21-jdk-jammy@sha256:25d1276565738d3c805e632a4542c3a7598866ef967f4def6544c15de3a74b14 AS jdk

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

ENV DEBIAN_FRONTEND=noninteractive \
    TERM=xterm-256color \
    JAVA_HOME=/opt/java/openjdk \
    PATH="/app/bin:/opt/java/openjdk/bin:/usr/local/go/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

WORKDIR /app

# 1. OS / agent-session packages (single apt transaction; pinned)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        ca-certificates=20230311+deb12u1 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        python-is-python3=3.11.2-1+deb12u1 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

# JDK from canonical Temurin (not apt OpenJDK)
COPY --from=jdk /opt/java/openjdk /opt/java/openjdk

# Agent-session smoke + toolchain presence
RUN tmux -V \
    && asciinema --version \
    && go version \
    && javac -version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

# 2. Verifier deps (pinned; offline at agent/verifier runtime)
RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

# 3. Module manifest (least volatile among project files)
COPY go.mod go.sum /app/

# 4. Stable ops / notes / config / fixtures / tools
COPY ops /app/ops
COPY config /app/config
COPY data /app/data
COPY --chmod=0755 tools/meshctl /app/tools/meshctl
COPY --chmod=0755 tools/readycheck /app/tools/readycheck
COPY --chmod=0755 tools/tmrebind /app/tools/tmrebind
COPY --chmod=0755 tools/bundlecopy /app/tools/bundlecopy
COPY --chmod=0755 tools/tmalias /app/tools/tmalias
COPY --chmod=0755 tools/tickplan /app/tools/tickplan

# 5. Volatile source (Go drivers + Java units + cmds)
COPY k9 /app/k9
COPY p7 /app/p7
COPY lane /app/lane
COPY seat /app/seat
COPY roll /app/roll
COPY cmd /app/cmd
COPY m2 /app/m2

# 6. Install entrypoints; warm probe once; drop build outputs for offline rebuild
RUN mkdir -p /app/bin /output \
    && install -D -m 0755 /app/tools/meshctl /app/bin/meshctl \
    && install -D -m 0755 /app/tools/readycheck /app/bin/readycheck \
    && install -D -m 0755 /app/tools/tmrebind /app/bin/tmrebind \
    && install -D -m 0755 /app/tools/bundlecopy /app/bin/bundlecopy \
    && install -D -m 0755 /app/tools/tmalias /app/bin/tmalias \
    && install -D -m 0755 /app/tools/tickplan /app/bin/tickplan \
    && /app/bin/readycheck \
    && /app/bin/meshctl probe || true \
    && rm -f /output/mesh-cutover.json \
    && rm -rf /app/m2/out /tmp/meshprobe-build

WORKDIR /app
