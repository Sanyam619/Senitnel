# syntax=docker/dockerfile:1
#
# Final runtime base: canonical Debian (Dockerfile & Image Best Practices §2).
# Builder stages donate digest-pinned Rust/Go toolchains so the agent can rebuild
# offline after editing source (allow_internet = false).

FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS rust_toolchain

FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS go_toolchain

FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.source="terminal-bench-3"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# 1. OS packages (tmux + asciinema required for agent sessions).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        tmux=3.3a-3 \
        ca-certificates=20230311+deb12u1 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        build-essential=12.9 \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color \
    LANG=C.UTF-8

RUN command -v tmux \
    && command -v asciinema \
    && tmux -V \
    && asciinema --version \
    && tmux new-session -d -s _smoke \
    && tmux has-session -t _smoke \
    && tmux kill-session -t _smoke

# 2. Verifier deps (baked in; test.sh must not network-install).
RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

# 3. Language toolchains for in-container rebuilds.
COPY --from=rust_toolchain /usr/local/cargo /usr/local/cargo
COPY --from=rust_toolchain /usr/local/rustup /usr/local/rustup
COPY --from=go_toolchain /usr/local/go /usr/local/go
ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH="/usr/local/cargo/bin:/usr/local/go/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    GOPROXY=off

WORKDIR /app

# 4. Manifests before volatile source (cache-friendly layering).
COPY Makefile /app/Makefile
COPY policy/Cargo.toml policy/Cargo.lock /app/policy/
COPY enroll/go.mod enroll/go.sum /app/enroll/

# 5. Source and task fixtures.
COPY include /app/include
COPY frame /app/frame
COPY policy/src /app/policy/src
COPY enroll/cmd /app/enroll/cmd
COPY enroll/internal /app/enroll/internal
COPY --chmod=0755 scripts/ /app/scripts/
COPY docs /app/docs
COPY data /app/data

# 6. Build tools into /app/bin so the baseline image is runnable.
RUN make \
    && mkdir -p /output \
    && command -v tmux \
    && command -v asciinema

WORKDIR /app
