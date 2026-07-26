FROM public.ecr.aws/docker/library/gcc:13-bookworm@sha256:930f2ebe239275fa67226654cb79273ea34eee672ae61c8a39f689c37fb7ac5c

# Agent runtime requires tmux and asciinema before COPY layers below.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates=20230311+deb12u1 \
        make=4.3-4.1 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
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
COPY docs/ /app/docs/
COPY data/ /app/data/

RUN chmod +x /app/scripts/run_restart.sh /app/scripts/inspect_archive.sh

RUN make clean && make
