# syntax=docker/dockerfile:1
#
# JPMS layered JNI desk (Java + JNI). Final runtime base is the sanctioned
# Terminal-Bench Java (JDK) canonical image (Dockerfile & Image Best Practices §2).
# Agent must rebuild after edits, so javac + gcc stay in the final stage (§6).

FROM public.ecr.aws/docker/library/eclipse-temurin:21-jdk-jammy@sha256:25d1276565738d3c805e632a4542c3a7598866ef967f4def6544c15de3a74b14

LABEL org.opencontainers.image.source="terminal-bench-3" \
      org.opencontainers.image.title="jpms-native-admit-lattice" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="MIT"

ENV DEBIAN_FRONTEND=noninteractive \
    TERM=xterm-256color \
    HOME=/tmp \
    TMUX_TMPDIR=/tmp \
    XDG_CONFIG_HOME=/tmp/.config \
    JAVA_HOME=/opt/java/openjdk \
    PATH="/opt/java/openjdk/bin:${PATH}"

WORKDIR /app

# 1. OS / agent session tools + rebuild toolchain + verifier Python (one apt transaction)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.1.0-1 \
        ca-certificates=20260601~22.04.1 \
        build-essential=12.9ubuntu3 \
        make=4.3-4.1build1 \
        python3=3.10.6-1~22.04.1 \
        python3-pip=22.0.2+dfsg-1ubuntu0.7 \
        python-is-python3=3.9.2-2 \
        tmux=3.2a-4ubuntu0.2 \
    && rm -rf /var/lib/apt/lists/*

# Agent session smoke (tmux + asciinema required at runtime)
RUN install -d -m 1777 /tmp \
    && install -d -m 0777 /tmp/.config /tmp/.config/asciinema \
    && tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

# 2. Verifier deps (pinned; offline at agent/verifier runtime — not installed in test.sh)
RUN pip3 install --no-cache-dir \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

# 3. Runtime directories used by helpers, fixtures, and harness logs
RUN mkdir -p /opt/desk/bin /opt/desk/lib /opt/desk/classes \
        /output /logs /logs/agent /logs/verifier /app/bin \
    && chmod 0777 /output /logs /logs/agent /logs/verifier /app /opt/desk

# 4. Build manifest before volatile source (cache-friendly layering)
COPY Makefile /app/Makefile
COPY include/ /app/include/

# 5. Source and task fixtures (narrow COPY — no COPY .)
COPY native/ /app/native/
COPY flux/ /app/flux/
COPY nest/ /app/nest/
COPY forge/ /app/forge/
COPY lib/ /app/lib/
COPY desk/ /app/desk/
COPY cmd/ /app/cmd/
COPY gate/ /app/gate/
COPY config/ /app/config/
COPY docs/ /app/docs/
COPY data/ /app/data/
COPY --chmod=0755 scripts/ /app/scripts/
COPY --chmod=0755 data/build_fixtures.sh /tmp/build_fixtures.sh

# 6. Build JPMS JNI bridge + Java desk; seal gate jar ahead of rebuildable classes
RUN make all \
    && make seal-gate \
    && make install \
    && test -f /opt/desk/lib/gate.jar \
    && test -f /opt/desk/lib/libpackjni.so \
    && test ! -f /app/gate/GateSeal.java \
    && /tmp/build_fixtures.sh \
    && rm -f /tmp/build_fixtures.sh \
    && java -version \
    && test -x /app/bin/surfcheck \
    && test -x /app/scripts/run-pack.sh \
    && test -f /opt/desk/lib/gate.jar

WORKDIR /app
