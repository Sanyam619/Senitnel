# Canonical Terminal-Bench Python runtime (digest-pinned).
FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# OS packages. JRE runs the sealed table judge; no JDK in the agent image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        ca-certificates=20230311+deb12u1 \
        openjdk-17-jre-headless=17.0.19+10-1~deb12u2 \
        procps=2:4.0.2-3 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
# pytest==8.4.1 and pytest-json-ctrf==0.3.5 come from the hashed lockfile.
RUN pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt
RUN rm /tmp/requirements.txt

RUN mkdir -p /app/bin /opt/tbench/puzzles /output
COPY fixtures/judge.jar /app/bin/judge.jar
COPY fixtures/judge.jar /opt/tbench/judge.jar
RUN chmod 0555 /app/bin/judge.jar \
    && chmod 0444 /opt/tbench/judge.jar

COPY puzzles/ /app/puzzles/
COPY puzzles/ /opt/tbench/puzzles/
COPY history/ /app/history/
COPY docs/ /app/docs/
COPY tools/ /app/tools/
COPY kiosk/ /app/kiosk/

RUN chmod 0555 /app/tools/sensei_hint.sh \
    && chmod 0555 /app/kiosk/emit_card.sh \
    && java -jar /app/bin/judge.jar view --board /app/puzzles/board_01.txt >/dev/null \
    && test "$(ls -1 /app/puzzles/board_*.txt | wc -l)" -eq 11

ENV TERM=xterm-256color
ENV PATH="/app/bin:${PATH}"
