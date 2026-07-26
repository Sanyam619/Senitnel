# syntax=docker/dockerfile:1
#
# Canonical Terminal-Bench Python runtime (dockerfile & image best practices §2):
#   public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

LABEL org.opencontainers.image.source="terminal-bench-3" \
      org.opencontainers.image.revision="contrastive-vl-alignment-eval" \
      org.opencontainers.image.created="2026-07-25T00:00:00Z" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Single apt transaction; pin versions; clean lists in-layer.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        ca-certificates=20230311+deb12u1 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color \
    PYTHONPATH=/app:/app/eval \
    PYTHONDONTWRITEBYTECODE=1

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

COPY requirements.txt /tmp/requirements.txt
# Installs pytest==8.4.1 and pytest-json-ctrf==0.3.5 with hash-locked transitive deps.
RUN python3 -m pip install --no-cache-dir --require-hashes \
    -r /tmp/requirements.txt
RUN rm -f /tmp/requirements.txt

COPY calib/ /app/calib/
COPY prism/ /app/prism/
COPY eval/ /app/eval/
COPY --chmod=0755 scripts/ /app/scripts/
COPY docs/ /app/docs/
COPY data/ /app/data/
COPY --chmod=0755 tools/ /app/tools/

RUN chmod 0755 /app/eval/refresh_seat.sh /app/scripts/run_vl_eval.sh /app/tools/vlprobe \
    && mkdir -p /output /logs/verifier
