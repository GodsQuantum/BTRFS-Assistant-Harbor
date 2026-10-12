#!/usr/bin/env python3
"""Isolated real Btrfs full/incremental send/receive regression on QEMU TCG.

Requires Alpine virt 3.23.3 ISO, QEMU x86_64, pexpect and a statically linked
musl build of harbor-transport. A disposable Btrfs disk and temporary 9p
share live only beneath a TemporaryDirectory and never mount on the LXC host.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import urllib.request

import pexpect

EXPECTED_ISO_SHA256 = "d91fb5c7a73528c89e0a1aa9a7d959f9deb9ca3dc5211e39bd73fd7df0d9070e"
ALPINE_VERSION = "3.23.3"
REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "target/x86_64-unknown-linux-musl/release/harbor-transport"

PREPARE = r"""#!/bin/sh
set -eu
mkfs.btrfs -fq /dev/vda
mkdir -p /mnt/fs
mount -t btrfs /dev/vda /mnt/fs
btrfs subvolume create /mnt/fs/work
mkdir -p /mnt/fs/work/docs
printf '%s\n' 'original' > /mnt/fs/work/docs/one.txt
chmod 640 /mnt/fs/work/docs/one.txt
ln /mnt/fs/work/docs/one.txt /mnt/fs/work/docs/hardlink.txt
ln -s one.txt /mnt/fs/work/docs/symlink.txt
setfattr -n user.harbor_test -v metadata-preserved /mnt/fs/work/docs/one.txt
truncate -s 16M /mnt/fs/work/sparse.bin
printf 'end' | dd of=/mnt/fs/work/sparse.bin bs=1 seek=16777213 conv=notrunc 2>/dev/null
dd if=/dev/urandom of=/mnt/fs/work/blob.bin bs=4096 count=32 2>/dev/null
btrfs subvolume create /mnt/fs/work/nested
printf '%s\n' 'subvolume content must not travel' > /mnt/fs/work/nested/secret.txt
sync
btrfs subvolume snapshot -r /mnt/fs/work /mnt/fs/base
printf '%s\n' 'edited' > /mnt/fs/work/docs/one.txt
printf '%s\n' 'additional' > /mnt/fs/work/docs/second.txt
rm /mnt/fs/work/blob.bin
sync
btrfs subvolume snapshot -r /mnt/fs/work /mnt/fs/next
cp /mnt/share/harbor-transport /tmp/harbor-transport
chmod 700 /tmp/harbor-transport
adduser -D -u 1000 harborbackup
export PKEXEC_UID=1000
mkdir -p /mnt/share/cas
/tmp/harbor-transport init --repo /mnt/share/cas --allow-local
test "$(stat -c %u /mnt/share/cas/.harbor-repo-id)" = 1000
/tmp/harbor-transport send --repo /mnt/share/cas --name base-vm --snapshot /mnt/fs/base --experimental --allow-local --retries 0
/tmp/harbor-transport send --repo /mnt/share/cas --name next-vm --snapshot /mnt/fs/next --parent /mnt/fs/base --parent-archive base-vm --experimental --allow-local --retries 0
/tmp/harbor-transport verify-stream --repo /mnt/share/cas --name base-vm
/tmp/harbor-transport verify-stream --repo /mnt/share/cas --name next-vm
test "$(stat -c %u /mnt/share/cas/manifests/base-vm.json)" = 1000
test "$(stat -c %u /mnt/share/cas/manifests/next-vm.json)" = 1000
mkdir -p /mnt/fs/received
/tmp/harbor-transport receive --repo /mnt/share/cas --name next-vm --staging /mnt/fs/received --preview
/tmp/harbor-transport receive --repo /mnt/share/cas --name next-vm --staging /mnt/fs/received --confirm
cmp /mnt/fs/work/docs/one.txt /mnt/fs/received/next/docs/one.txt
cmp /mnt/fs/work/docs/second.txt /mnt/fs/received/next/docs/second.txt
cmp /mnt/fs/work/sparse.bin /mnt/fs/received/next/sparse.bin
test "$(stat -c %a /mnt/fs/received/next/docs/one.txt)" = "640"
test "$(readlink /mnt/fs/received/next/docs/symlink.txt)" = "one.txt"
test "$(stat -c %i /mnt/fs/received/next/docs/one.txt)" = "$(stat -c %i /mnt/fs/received/next/docs/hardlink.txt)"
getfattr -n user.harbor_test /mnt/fs/received/next/docs/one.txt | grep -q metadata-preserved
test ! -e /mnt/fs/received/next/nested/secret.txt
btrfs property get -ts /mnt/fs/received/next ro | grep -q 'ro=true'
echo HARBOR_FULL_AND_INCREMENTAL_RECEIVE_VERIFIED
"""

NEGATIVE = r"""#!/bin/sh
set -eu
mkdir -p /mnt/fs/negative-corrupt /mnt/fs/negative-parent
if /tmp/harbor-transport receive --repo /mnt/share/cas-corrupt --name next-vm --staging /mnt/fs/negative-corrupt --confirm; then
    echo CORRUPT_WAS_ACCEPTED
    exit 21
fi
test -z "$(ls -A /mnt/fs/negative-corrupt)"
if /tmp/harbor-transport receive --repo /mnt/share/cas-no-parent --name next-vm --staging /mnt/fs/negative-parent --confirm; then
    echo MISSING_PARENT_WAS_ACCEPTED
    exit 22
fi
test -z "$(ls -A /mnt/fs/negative-parent)"
/tmp/harbor-transport verify --repo /mnt/share/cas --name next-vm
echo HARBOR_NEGATIVE_TESTS_FAIL_CLOSED
"""

PRUNE = r"""#!/bin/sh
set -eu
# An incremental's required base must never disappear, even with explicit intent.
if /tmp/harbor-transport prune --repo /mnt/share/cas --name base-vm; then
    echo DELETED_REQUIRED_PARENT
    exit 31
fi
/tmp/harbor-transport verify-stream --repo /mnt/share/cas --name next-vm
/tmp/harbor-transport prune --repo /mnt/share/cas --name next-vm > /tmp/plan.json
token="$(jq -r '.plan.plan_sha256' /tmp/plan.json)"
test "${#token}" = 64
if /tmp/harbor-transport prune --repo /mnt/share/cas --name next-vm --confirm-plan "$(printf 'f%.0s' $(seq 1 64))"; then
    echo STALE_TOKEN_ACCEPTED
    exit 32
fi
/tmp/harbor-transport prune --repo /mnt/share/cas --name next-vm --confirm-plan "$token"
test ! -e /mnt/share/cas/manifests/next-vm.json
/tmp/harbor-transport verify-stream --repo /mnt/share/cas --name base-vm
mkdir -p /mnt/fs/gc-restored
/tmp/harbor-transport receive --repo /mnt/share/cas --name base-vm --staging /mnt/fs/gc-restored --confirm
printf '%s\n' 'original' | cmp - /mnt/fs/gc-restored/base/docs/one.txt
test "$(readlink /mnt/fs/gc-restored/base/docs/symlink.txt)" = "one.txt"
echo HARBOR_PRUNE_PRESERVES_PARENT_AND_RESTORE
"""

def require_binary(path: str) -> None:
    if not shutil.which(path):
        raise RuntimeError(f"Required tool is missing: {path}")

def extract_iso(iso: Path, root: Path) -> None:
    actual = hashlib.sha256(iso.read_bytes()).hexdigest()
    if actual != EXPECTED_ISO_SHA256:
        raise ValueError(f"Alpine ISO SHA mismatch: {actual}")
    subprocess.run(
        ["7z", "e", "-y", f"-o{root}", str(iso),
         "boot/vmlinuz-virt", "boot/initramfs-virt"],
        check=True, stdout=subprocess.DEVNULL,
    )

def run_guest(child: pexpect.spawn, script_path: str, label: str, timeout: int = 150) -> None:
    marker = f"__HARBOR_{label}_SUCCESS__"
    child.sendline(f"sh /mnt/share/{script_path} && echo {marker}".encode())
    child.expect(marker.encode(), timeout=timeout)
    child.expect(r"localhost:~#", timeout=15)
    print(f"PASS {label}", flush=True)

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", type=Path, help="Previously downloaded Alpine virt ISO; fetched into disposable scratch if omitted")
    parser.add_argument("--binary", type=Path, default=BIN)
    parser.add_argument("--temp-root", type=Path, default=Path(tempfile.gettempdir()))
    args = parser.parse_args()
    for tool in ("qemu-system-x86_64", "7z"):
        require_binary(tool)
    if not args.binary.is_file():
        raise ValueError("Build static musl harbor-transport before running VM E2E")
    with tempfile.TemporaryDirectory(prefix=".harbor-guest-e2e-", dir=args.temp_root) as temp:
        work = Path(temp)
        share = work / "share"
        share.mkdir()
        iso = args.iso
        if iso is None:
            iso = work / "alpine.iso"
            url = f"https://dl-cdn.alpinelinux.org/alpine/v3.23/releases/x86_64/alpine-virt-{ALPINE_VERSION}-x86_64.iso"
            with urllib.request.urlopen(url, timeout=60) as response, iso.open("wb") as output:
                shutil.copyfileobj(response, output)
        extract_iso(iso, work)
        (work / "disk.raw").write_bytes(b"")
        subprocess.run(["truncate", "-s", "640M", str(work / "disk.raw")], check=True)
        shutil.copy2(args.binary, share / "harbor-transport")
        (share / "prepare.sh").write_text(PREPARE)
        (share / "negative.sh").write_text(NEGATIVE)
        (share / "prune.sh").write_text(PRUNE)
        qemu = [
            "qemu-system-x86_64", "-machine", "q35,accel=tcg", "-cpu", "qemu64",
            "-m", "768", "-smp", "2",
            "-kernel", str(work / "vmlinuz-virt"),
            "-initrd", str(work / "initramfs-virt"),
            "-append", "console=ttyS0,115200 alpine_dev=sr0",
            "-cdrom", str(iso),
            "-drive", f"file={work / 'disk.raw'},format=raw,if=virtio",
            "-virtfs", f"local,path={share},security_model=none,mount_tag=hostshare,id=host0",
            "-netdev", "user,id=n0", "-device", "virtio-net-pci,netdev=n0",
            "-display", "none", "-serial", "stdio", "-monitor", "none", "-no-reboot",
        ]
        logfile = (work / "guest-console.log").open("wb")
        child = pexpect.spawn(qemu[0], qemu[1:], encoding=None, timeout=150)
        child.logfile = logfile
        try:
            child.expect(b"localhost login:", timeout=150)
            child.sendline(b"root")
            child.expect(b"localhost:~#", timeout=40)
            child.sendline(b"stty -echo")
            child.expect(b"localhost:~#", timeout=15)
            child.sendline(b"ip link set eth0 up; udhcpc -i eth0 -q; echo https://dl-cdn.alpinelinux.org/alpine/v3.23/main > /etc/apk/repositories; apk add --no-cache btrfs-progs coreutils attr jq >/tmp/apk.log; mkdir -p /mnt/share; mount -t 9p -o trans=virtio,version=9p2000.L hostshare /mnt/share; echo __GUEST_READY__")
            child.expect(b"__GUEST_READY__", timeout=150)
            child.expect(b"localhost:~#", timeout=15)
            run_guest(child, "prepare.sh", "FULL_INCREMENTAL", 180)
            shutil.copytree(share / "cas", share / "cas-corrupt")
            shutil.copytree(share / "cas", share / "cas-no-parent")
            obj = next((share / "cas-corrupt" / "objects").glob("*/*.zst"))
            obj.write_bytes(b"corrupted")
            (share / "cas-no-parent" / "manifests/base-vm.json").unlink()
            run_guest(child, "negative.sh", "FAIL_CLOSED", 120)
            run_guest(child, "prune.sh", "PRUNE_RESTORE", 150)
            child.sendline(b"poweroff")
            child.expect(pexpect.EOF, timeout=45)
            print("PASS E2E QEMU BTRFS ISOLATED", flush=True)
        except BaseException:
            logfile.flush()
            print(f"VM test failed; guest log tail: {work / 'guest-console.log'}", flush=True)
            raise
        finally:
            if child.isalive():
                child.terminate(force=True)
            logfile.close()

if __name__ == "__main__":
    main()
