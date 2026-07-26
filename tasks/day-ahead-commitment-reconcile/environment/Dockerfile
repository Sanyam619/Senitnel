FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        ca-certificates=20230311+deb12u1 \
        openjdk-17-jre-headless=17.0.19+10-1~deb12u2 \
        procps=2:4.0.2-3 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

ENV TERM=xterm-256color

WORKDIR /opt/distro

COPY distro/ /opt/distro/
COPY data_fixtures/ /data/fixtures/
COPY data_staging/ /data/staging/
COPY fixtures/rowcheck.jar /opt/distro/lib/rowcheck.jar

RUN mkdir -p /data/out \
    && java -jar /opt/distro/lib/rowcheck.jar validate --board /data/fixtures/board_01.txt \
        --claim '{"status":"feasible_clear","cleared":[{"unit_id":"A","mw":15,"offer_price":10},{"unit_id":"B","mw":50,"offer_price":18},{"unit_id":"D","mw":25,"offer_price":12}],"smp":18,"reserve_binds":false}' \
        >/dev/null \
    && sha256sum /opt/distro/lib/rowcheck.jar | awk '{print $1}' > /opt/distro/lib/rowcheck.jar.sha256 \
    && chmod 0555 /opt/distro/lib/rowcheck.jar /opt/distro/scripts/run-cycle.sh \
    && chmod 0444 /opt/distro/lib/rowcheck.jar.sha256 \
    && test "$(ls -1 /data/fixtures/board_*.txt | wc -l)" -eq 12

ENV PATH="/opt/distro/scripts:${PATH}"
ENV PYTHONPATH="/opt/distro"
ENV DISTRO_ROOT="/opt/distro"
ENV FIXTURE_ROOT="/data/fixtures"
