# Canonical Terminal-Bench Python runtime (digest-pinned).
# Sanctioned base: python:3.13-slim-bookworm (Dockerfile & Image Best Practices §2).
FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# 1. OS packages (least volatile). JRE runs the sealed table judge; no JDK.
#    tmux + asciinema required by the agent runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        ca-certificates=20230311+deb12u1 \
        openjdk-17-jre-headless=17.0.19+10-1~deb12u2 \
        procps=2:4.0.2-3 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

# 2. Verifier Python deps from hashed lockfile (offline; allow_internet=false).
# pytest==8.4.1 and pytest-json-ctrf==0.3.5 come from the hashed lockfile.
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt
RUN rm /tmp/requirements.txt

# 3. Sealed referee + verifier-owned copy (narrow COPY, not COPY .).
RUN mkdir -p /app/bin /opt/tbench/puzzles /output
COPY --chmod=0555 fixtures/judge.jar /app/bin/judge.jar
COPY --chmod=0444 fixtures/judge.jar /opt/tbench/judge.jar

# 4. Task materials (most volatile last).
COPY puzzles/ /app/puzzles/
COPY puzzles/ /opt/tbench/puzzles/
COPY history/ /app/history/
COPY docs/ /app/docs/
COPY --chmod=0555 tools/sensei_hint.sh /app/tools/sensei_hint.sh
COPY kiosk/ /app/kiosk/
RUN chmod 0555 /app/kiosk/emit_card.sh \
    && java -jar /app/bin/judge.jar view --board /app/puzzles/board_01.txt >/dev/null \
    && test "$(ls -1 /app/puzzles/board_*.txt | wc -l)" -eq 10

ENV TERM=xterm-256color
ENV PATH="/app/bin:${PATH}"
