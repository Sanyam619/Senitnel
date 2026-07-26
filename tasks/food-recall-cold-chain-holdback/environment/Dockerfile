# syntax=docker/dockerfile:1

FROM public.ecr.aws/docker/library/maven:3.9.9-eclipse-temurin-21@sha256:3a4ab3276a087bf276f79cae96b1af04f53731bec53fb2e651aca79e4b10211e AS builder

WORKDIR /build
COPY pom.xml .
COPY mod-p3 ./mod-p3
COPY mod-m7 ./mod-m7
COPY mod-k9 ./mod-k9
COPY app-module ./app-module
COPY config ./config
RUN mvn -q package -Dmaven.test.skip=true

FROM public.ecr.aws/docker/library/eclipse-temurin:21-jdk-jammy@sha256:25d1276565738d3c805e632a4542c3a7598866ef967f4def6544c15de3a74b14

LABEL org.opencontainers.image.source="https://github.com/laude-institute/terminal-bench"
LABEL org.opencontainers.image.licenses="Apache-2.0"

# Agent runtime requires tmux and asciinema before any other setup.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema \
        tmux \
        ca-certificates=20260601~22.04.1 \
        python3=3.10.6-1~22.04.1 \
        python3-pip=22.0.2+dfsg-1ubuntu0.7 \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color

RUN tmux -V && asciinema --version

RUN pip3 install --no-cache-dir \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY --from=builder /build/mod-p3/target/classes /opt/distro/mod-p3/target/classes
COPY --from=builder /build/mod-m7/target/classes /opt/distro/mod-m7/target/classes
COPY --from=builder /build/mod-k9/target/classes /opt/distro/mod-k9/target/classes
COPY --from=builder /build/app-module/target/classes /opt/distro/app-module/target/classes
COPY --from=builder /build/app-module/target/cycle-batch-1.0.0.jar /opt/distro/target/cycle-batch-1.0.0.jar
COPY pom.xml /opt/distro/pom.xml
COPY mod-p3 /opt/distro/mod-p3
COPY mod-m7 /opt/distro/mod-m7
COPY mod-k9 /opt/distro/mod-k9
COPY app-module /opt/distro/app-module
COPY config /opt/distro/config
COPY --chmod=0755 scripts /opt/distro/scripts/
COPY --from=builder /build/app-module/target /opt/distro/app-module/target

RUN /opt/distro/scripts/build_fixtures.sh

WORKDIR /opt/distro
