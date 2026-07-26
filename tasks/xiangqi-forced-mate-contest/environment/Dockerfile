# Sanctioned Terminal-Bench final runtime base (Dockerfile & Image Best Practices §2).
# Exact digest-pinned Python canonical — required by check_pinned_images +
# check_sanctioned_base_images.
FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# 1. OS packages (least volatile). Agent runtime requires tmux + asciinema.
# JRE is enough to run the sealed judge.jar; no JDK toolchain in the image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        ca-certificates=20230311+deb12u1 \
        openjdk-17-jre-headless=17.0.19+10-1~deb12u2 \
        procps=2:4.0.2-3 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

# 2. Verifier Python deps from hashed lockfile (pytest discovered via comment).
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt
RUN rm -f /tmp/requirements.txt

ENV TERM=xterm-256color
ENV HOME=/tmp

WORKDIR /app

# 3. Task files — narrow COPY; permissions via --chmod (no recursive /app rewrite).
COPY --chmod=0555 fixtures/judge.jar /app/bin/judge.jar
COPY --chmod=0444 fixtures/judge.jar /opt/tbench/judge.jar
COPY puzzles/ /app/puzzles/
COPY --chmod=0444 puzzles/ /opt/tbench/puzzles/
COPY history/ /app/history/
COPY docs/ /app/docs/
COPY --chmod=0555 tools/sensei_hint.sh /app/tools/sensei_hint.sh
COPY kiosk/sheet_load.py /app/kiosk/sheet_load.py
COPY kiosk/xqlib.py /app/kiosk/xqlib.py
COPY kiosk/draft.py /app/kiosk/draft.py
COPY --chmod=0555 kiosk/emit_card.sh /app/kiosk/emit_card.sh

# Non-root agent (uid 65534) needs write access to /app and /output; not recursive.
RUN mkdir -p /output \
    && chmod 0777 /app /output \
    && java -jar /app/bin/judge.jar view --board /app/puzzles/board_01.txt >/dev/null \
    && test "$(ls -1 /app/puzzles/board_*.txt | wc -l)" -eq 12

ENV PATH="/app/bin:${PATH}"
