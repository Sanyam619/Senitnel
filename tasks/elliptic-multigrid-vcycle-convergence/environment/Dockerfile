FROM public.ecr.aws/docker/library/gcc:13-bookworm@sha256:930f2ebe239275fa67226654cb79273ea34eee672ae61c8a39f689c37fb7ac5c

LABEL org.opencontainers.image.title="elliptic-multigrid-vcycle-convergence"
LABEL org.opencontainers.image.description="Edition 2 task environment: 2D variable-coefficient elliptic multigrid V-cycle solver"
LABEL org.opencontainers.image.source="https://github.com/laude-institute/terminal-bench"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.revision="1"
LABEL org.opencontainers.image.created="2026-07-11"
LABEL org.opencontainers.image.licenses="MIT"

ENV TERM=xterm-256color

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        ca-certificates=20230311+deb12u1 \
        make=4.3-4.1 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

RUN tmux -V && asciinema --version

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

WORKDIR /app

COPY Makefile /app/Makefile
COPY include/ /app/include/
COPY src/ /app/src/
COPY scripts/ /app/scripts/
COPY data/ /app/data/
COPY docs/ /app/docs/
COPY tools/ /app/tools/

RUN chmod +x /app/scripts/run_solve.sh

RUN make clean && make
