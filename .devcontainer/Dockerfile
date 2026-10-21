FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake ninja-build pkg-config git jq curl \
    clang clang-format clang-tidy gdb \
    qt6-base-dev qt6-tools-dev qt6-tools-dev-tools qt6-wayland \
    libbtrfsutil-dev btrfs-progs snapper zstd libzstd-dev musl-tools \
    python3 python3-venv python3-filelock python3-rich python3-pexpect \
    qemu-system-x86 p7zip-full \
    && rm -rf /var/lib/apt/lists/*
# No privileged Docker/KVM, no host filesystem mounts, no embedded credentials.
