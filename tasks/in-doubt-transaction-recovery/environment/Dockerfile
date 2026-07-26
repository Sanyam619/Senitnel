FROM public.ecr.aws/docker/library/eclipse-temurin:21-jdk-jammy@sha256:25d1276565738d3c805e632a4542c3a7598866ef967f4def6544c15de3a74b14

LABEL org.opencontainers.image.source="com.acme.ops-recovery-console" \
    org.opencontainers.image.title="Acme Ops Recovery Console" \
    org.opencontainers.image.revision="local" \
    org.opencontainers.image.created="2026-07-02" \
    org.opencontainers.image.version="1.0" \
    org.opencontainers.image.licenses="UNLICENSED"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.1.0-1 \
        ca-certificates=20260601~22.04.1 \
        python3=3.10.6-1~22.04.1 \
        python3-pip=22.0.2+dfsg-1ubuntu0.7 \
        tmux=3.2a-4ubuntu0.2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
# Installs pytest==8.4.1 and pytest-json-ctrf==0.3.5 with hash-locked transitive deps.
RUN python3 -m pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt
RUN rm -f /tmp/requirements.txt

COPY --chmod=0755 build.sh /app/build.sh
COPY README.md /app/README.md
COPY ops/ /app/ops/
COPY k7/ /app/k7/
COPY m3/ /app/m3/
COPY r9/ /app/r9/
COPY w2/ /app/w2/
COPY src/ /app/src/
COPY scenarios/ /app/scenarios/
WORKDIR /app
RUN chmod +x /app/ops/tools/replay.sh /app/k7/*.py /app/m3/*.py /app/r9/*.py /app/w2/*.py
