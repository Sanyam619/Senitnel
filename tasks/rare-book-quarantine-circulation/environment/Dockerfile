# syntax=docker/dockerfile:1

# Builder — canonical Maven image (dockerfile and image best practices §2)
FROM public.ecr.aws/docker/library/maven:3.9.9-eclipse-temurin-21@sha256:3a4ab3276a087bf276f79cae96b1af04f53731bec53fb2e651aca79e4b10211e AS builder

WORKDIR /build
COPY pom.xml .
COPY src ./src
COPY config ./config
RUN mvn -q package

# Runtime — canonical Java JDK image; offline rebuild uses cached .m2 from builder
FROM public.ecr.aws/docker/library/eclipse-temurin:21-jdk-jammy@sha256:25d1276565738d3c805e632a4542c3a7598866ef967f4def6544c15de3a74b14

# Agent session stack (tmux, asciinema) plus verifier runtime in one apt transaction.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
        bash \
        ca-certificates \
        procps \
        python3 \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

RUN tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

COPY --from=builder /root/.m2 /root/.m2
COPY --from=builder /usr/share/maven /usr/share/maven
ENV MAVEN_HOME=/usr/share/maven
ENV PATH="/usr/share/maven/bin:${PATH}"
ENV TERM=xterm-256color

COPY pom.xml /opt/archives/pom.xml
COPY src /opt/archives/src
COPY config /opt/archives/config
COPY scripts /opt/archives/scripts/
COPY --from=builder /build/target /opt/archives/target

RUN chmod +x /opt/archives/scripts/*.sh \
    && /opt/archives/scripts/build_fixtures.sh

WORKDIR /opt/archives
