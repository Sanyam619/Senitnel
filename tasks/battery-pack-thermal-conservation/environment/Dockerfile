# syntax=docker/dockerfile:1
# Canonical Terminal-Bench Python runtime (see dockerfile and image best practices.mdc §2).

FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

WORKDIR /app

LABEL org.opencontainers.image.source="tasks/battery-pack-thermal-conservation" \
      org.opencontainers.image.title="battery-pack-thermal-conservation" \
      org.opencontainers.image.version="2.0" \
      org.opencontainers.image.licenses="Apache-2.0"

# 1. OS / agent-session packages (pinned; single apt layer).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        ca-certificates=20230311+deb12u1 \
        procps=2:4.0.2-3 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

# 2. Verifier Python deps (pinned; baked for allow_internet=false).
RUN pip install --no-cache-dir \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

# 3. Task source (narrow COPY — no solution/ or tests/).
COPY config/ /app/config/
COPY data/ /app/data/
COPY docs/ /app/docs/
COPY knit_x/ /app/knit_x/
COPY fold_y/ /app/fold_y/
COPY slot_z/ /app/slot_z/
COPY solver/ /app/solver/
COPY scripts/ /app/scripts/
COPY tools/ /app/tools/

# 4. Runtime layout: package markers + thermalsurf on PATH.
RUN mkdir -p /output /app/bin \
    && touch /app/solver/__init__.py /app/solver/core/__init__.py \
      /app/knit_x/__init__.py /app/fold_y/__init__.py \
      /app/slot_z/__init__.py /app/solver/decoy/__init__.py \
    && cp /app/tools/thermalsurf /app/bin/thermalsurf \
    && chmod 0555 /app/scripts/run_thermal_eval.sh /app/scripts/prep_eval.sh /app/bin/thermalsurf

ENV PYTHONPATH=/app
ENV PATH="/app/bin:/app/scripts:${PATH}"
