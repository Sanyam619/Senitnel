# Offline image (allow_internet=false): Rust toolchain copied from builder stage;
# final runtime uses canonical public.ecr.aws python:3.13-slim-bookworm (see dockerfile and image best practices.mdc §2).
# Agent session: tmux + asciinema via apt (required — missing either breaks all agent runs).
FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS rust-base

FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

# Agent session tools in a dedicated layer (tmux + asciinema required for agent runs).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        libevent-core-2.1-7=2.1.12-stable-8 \
        libutempter0=1.2.1-3 \
        tmux=3.3a-3 \
    && apt-mark manual \
        tmux asciinema libevent-core-2.1-7 libutempter0 \
    && rm -rf /var/lib/apt/lists/* \
    && install -d -m 1777 /tmp \
    && install -d -m 0777 /root /tmp/.config /tmp/.config/asciinema \
    && test -x /usr/bin/tmux \
    && test -x /usr/bin/asciinema \
    && tmux -V \
    && asciinema --version \
    && HOME=/tmp TMUX_TMPDIR=/tmp TERM=xterm-256color XDG_CONFIG_HOME=/tmp/.config \
        tmux new-session -d -s _tb_image_check sleep 5 \
    && HOME=/tmp TMUX_TMPDIR=/tmp tmux kill-session -t _tb_image_check

# Rust build deps — re-pin session tools after apt churn.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        build-essential=12.9 \
        ca-certificates=20230311+deb12u1 \
        libevent-core-2.1-7=2.1.12-stable-8 \
        libutempter0=1.2.1-3 \
        tmux=3.3a-3 \
    && apt-mark manual \
        tmux asciinema libevent-core-2.1-7 libutempter0 \
    && rm -rf /var/lib/apt/lists/* \
    && install -d -m 1777 /tmp \
    && install -d -m 0777 /root /tmp/.config /tmp/.config/asciinema \
    && test -x /usr/bin/tmux \
    && test -x /usr/bin/asciinema \
    && tmux -V \
    && asciinema --version \
    && HOME=/tmp TMUX_TMPDIR=/tmp TERM=xterm-256color XDG_CONFIG_HOME=/tmp/.config \
        tmux new-session -d -s _tb_os_check sleep 5 \
    && HOME=/tmp TMUX_TMPDIR=/tmp tmux kill-session -t _tb_os_check

COPY --chmod=ugo+rwX --from=rust-base /usr/local/cargo /usr/local/cargo
COPY --chmod=ugo+rwX --from=rust-base /usr/local/rustup /usr/local/rustup
RUN ln -sf /usr/local/cargo/bin/cargo /usr/bin/cargo \
    && ln -sf /usr/local/cargo/bin/rustc /usr/bin/rustc \
    && chmod a+w /usr/local/cargo /usr/local/rustup \
    && test -x /usr/bin/tmux \
    && test -x /usr/bin/asciinema \
    && HOME=/tmp TMUX_TMPDIR=/tmp TERM=xterm-256color XDG_CONFIG_HOME=/tmp/.config \
        tmux new-session -d -s _tb_rust_check sleep 5 \
    && HOME=/tmp TMUX_TMPDIR=/tmp tmux kill-session -t _tb_rust_check

WORKDIR /app

ENV RUSTUP_HOME=/usr/local/rustup
ENV CARGO_HOME=/usr/local/cargo
ENV HOME=/tmp
ENV TMUX_TMPDIR=/tmp
ENV TERM=xterm-256color
ENV XDG_CONFIG_HOME=/tmp/.config
ENV SOURCE_DATE_EPOCH=0
ENV CARGO_TARGET_DIR=/app/target
ENV PATH="/app/bin:/usr/local/cargo/bin:/usr/local/bin:/usr/bin:/bin"

RUN ln -sf /usr/local/bin/python3.13 /usr/bin/python3 \
    && ln -sf /usr/local/bin/python3.13 /usr/bin/python

# Verifier deps — pip asciinema required after python3 symlink (apt wrapper targets system python).
COPY verifier-requirements.txt /opt/verifier-requirements.txt
RUN python3 -m pip install --no-cache-dir --break-system-packages \
        -r /opt/verifier-requirements.txt

RUN ln -sf /usr/local/bin/asciinema /usr/bin/asciinema

RUN rm -rf /root/.cache/pip \
    && python3 -m pytest --version \
    && test -x /usr/bin/tmux \
    && test -x /usr/bin/asciinema \
    && tmux -V \
    && asciinema --version \
    && /usr/bin/asciinema --version \
    && HOME=/tmp TMUX_TMPDIR=/tmp TERM=xterm-256color XDG_CONFIG_HOME=/tmp/.config \
        tmux new-session -d -s _tb_pip_check sleep 5 \
    && HOME=/tmp TMUX_TMPDIR=/tmp tmux kill-session -t _tb_pip_check

# Project manifests (least volatile).
COPY Cargo.toml /app/Cargo.toml
RUN cargo generate-lockfile

COPY src /app/src
COPY mk3 /app/mk3
COPY mk5 /app/mk5
COPY mk8 /app/mk8
COPY mk2 /app/mk2
COPY mk1 /app/mk1
COPY decoykit /app/decoykit
RUN cargo fetch --locked \
    && test -x /usr/bin/tmux \
    && test -x /usr/bin/asciinema \
    && HOME=/tmp TMUX_TMPDIR=/tmp TERM=xterm-256color XDG_CONFIG_HOME=/tmp/.config \
        tmux new-session -d -s _tb_fetch_check sleep 5 \
    && HOME=/tmp TMUX_TMPDIR=/tmp tmux kill-session -t _tb_fetch_check

# Agent-writable sources (narrow COPY; never solution/ or tests/).
COPY --chmod=0755 scripts /app/scripts
COPY config /app/config
COPY data /app/data
COPY schemas /app/schemas
COPY ops /app/ops
COPY dashboard /app/dashboard

# Warm build, drop build caches, and verify tmux survives compilation in the same layer.
RUN install -d -m 0777 /app/output /app/bin \
    && bash /app/scripts/build.sh \
    && rm -rf /app/target /root/.cache/cargo \
    && command -v /app/bin/frtl_audit \
    && test -x /usr/bin/tmux \
    && test -x /usr/bin/asciinema \
    && tmux -V \
    && asciinema --version \
    && HOME=/tmp TMUX_TMPDIR=/tmp TERM=xterm-256color XDG_CONFIG_HOME=/tmp/.config \
        tmux new-session -d -s _tb_final_check sleep 5 \
    && HOME=/tmp TMUX_TMPDIR=/tmp tmux kill-session -t _tb_final_check \
    && install -d -m 1777 /tmp \
    && install -d -m 0777 /root /tmp/.config /tmp/.config/asciinema \
    && HOME=/tmp TMUX_TMPDIR=/tmp TERM=xterm-256color XDG_CONFIG_HOME=/tmp/.config \
        tmux kill-server 2>/dev/null || true \
    && tmux new-session -d -s _tb_agent_boot sleep 5 \
    && tmux has-session -t _tb_agent_boot \
    && HOME=/tmp TMUX_TMPDIR=/tmp tmux kill-session -t _tb_agent_boot

ENV PATH="/app/bin:${PATH}"

# Final agent-runtime gate: re-pin tmux/asciinema after full image build; restore pip asciinema wrapper.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        libevent-core-2.1-7=2.1.12-stable-8 \
        libutempter0=1.2.1-3 \
        tmux=3.3a-3 \
    && apt-mark manual \
        tmux asciinema libevent-core-2.1-7 libutempter0 \
    && rm -rf /var/lib/apt/lists/* \
    && install -d -m 1777 /tmp \
    && install -d -m 0777 /root /tmp/.config /tmp/.config/asciinema \
    && ln -sf /usr/local/bin/asciinema /usr/bin/asciinema \
    && test -x /usr/bin/tmux \
    && test -x /usr/bin/asciinema \
    && tmux -V \
    && asciinema --version \
    && /usr/bin/asciinema --version \
    && HOME=/tmp TMUX_TMPDIR=/tmp TERM=xterm-256color XDG_CONFIG_HOME=/tmp/.config \
        tmux kill-server 2>/dev/null || true \
    && tmux new-session -d -s _tb_agent_boot sleep 5 \
    && tmux has-session -t _tb_agent_boot \
    && HOME=/tmp TMUX_TMPDIR=/tmp tmux kill-session -t _tb_agent_boot

# Re-apply /tmp session prerequisites and verify tmux/asciinema at container start (platforms may remount /tmp).
CMD ["bash", "-c", "install -d -m 1777 /tmp && install -d -m 0777 /root /tmp/.config /tmp/.config/asciinema && export HOME=/tmp TMUX_TMPDIR=/tmp TERM=xterm-256color XDG_CONFIG_HOME=/tmp/.config && test -x /usr/bin/tmux && test -x /usr/bin/asciinema && asciinema --version && tmux kill-server 2>/dev/null || true && tmux new-session -d -s _tb_boot sleep 1 && tmux has-session -t _tb_boot && tmux kill-session -t _tb_boot && exec sleep infinity"]
