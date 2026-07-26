# Canonical Java (JDK) runtime — Dockerfile & Image Best Practices §2
# public.ecr.aws/docker/library/eclipse-temurin:21-jdk-jammy
FROM public.ecr.aws/docker/library/eclipse-temurin:21-jdk-jammy@sha256:25d1276565738d3c805e632a4542c3a7598866ef967f4def6544c15de3a74b14

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

ENV DEBIAN_FRONTEND=noninteractive \
    TERM=xterm-256color \
    JAVA_HOME=/opt/java/openjdk \
    PATH="/app/bin:/opt/java/openjdk/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

WORKDIR /app

# 1. OS / agent session tools + JNI compile toolchain (single apt transaction).
# Agent must rebuild the shared library offline, so gcc/libc headers stay in the
# final image (Dockerfile & Image Best Practices §6 / §7).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.1.0-1 \
        ca-certificates=20260601~22.04.1 \
        gcc=4:11.2.0-1ubuntu1 \
        libc6-dev=2.35-0ubuntu3.13 \
        make=4.3-4.1build1 \
        python3=3.10.6-1~22.04.1 \
        python3-pip=22.0.2+dfsg-1ubuntu0.7 \
        python-is-python3=3.9.2-2 \
        tmux=3.2a-4ubuntu0.2 \
    && rm -rf /var/lib/apt/lists/*

RUN tmux -V \
    && asciinema --version \
    && javac -version \
    && gcc --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

# 2. Verifier deps (pinned; offline at agent/verifier runtime)
RUN pip3 install --no-cache-dir \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

# 3. Stable ops / notes / config / fixtures (less volatile)
COPY ops /app/ops
COPY link /app/link
COPY config /app/config
COPY data /app/data
COPY tools/packctl /app/tools/packctl

# 4. Source units and packaging drivers (more volatile)
COPY unit /app/unit
COPY k9 /app/k9
COPY p7 /app/p7
COPY m2 /app/m2
COPY native /app/native

# 5. Install probe entrypoint; warm packaging once so JDK/gcc paths are exercised,
# then drop build outputs so the agent rebuilds offline from sources.
RUN chmod 0755 /app/tools/packctl \
    && mkdir -p /app/bin /output \
    && install -D -m 0755 /app/tools/packctl /app/bin/packctl \
    && /app/bin/packctl \
    && rm -rf /app/build \
    && rm -f /app/native/libhelixhook.so /app/native/libhelixhook.dylib /output/pack-report.json

WORKDIR /app
