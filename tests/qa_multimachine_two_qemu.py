#!/usr/bin/env python3
"""Two separate disposable Alpine/QEMU Linux clients, one shared Harbor CAS.

Requires a verified Alpine virt ISO, a freshly built static musl transport,
pexpect, 7z and qemu-system-x86_64. Never touches real workstations or
production repositories. Remote 9p GC is intentionally refused; local Btrfs
GC is tested in the second guest on a disposable virtual disk.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import tempfile

import pexpect

ISO_SHA256 = "d91fb5c7a73528c89e0a1aa9a7d959f9deb9ca3dc5211e39bd73fd7df0d9070e"

PEGASUS = r"""#!/bin/sh
set -eu
adduser -D -u 1000 harborbackup
cp /mnt/share/harbor-transport /tmp/harbor-transport
chmod 700 /tmp/harbor-transport
export PKEXEC_UID=1000
repo=/mnt/share/Workstations
/tmp/harbor-transport init --repo "$repo" --allow-local > /mnt/share/init.json
/tmp/harbor-transport ingest-file --repo "$repo" --machine Pegasus --name root-1 --file /mnt/share/payload.bin --experimental --allow-local > /mnt/share/pegasus.json
test "$(jq -r '.new_objects' /mnt/share/pegasus.json)" -gt 0
test -f "$repo/machines/Pegasus/manifests/root-1.json"
test ! -e "$repo/machines/Pegasus/objects"
/tmp/harbor-transport verify --repo "$repo" --name m@Pegasus@root-1
echo PEGASUS_FIRST_GUEST_SUCCESS
"""

GALACTICA = r"""#!/bin/sh
set -eu
adduser -D -u 1000 harborbackup
cp /mnt/share/harbor-transport /tmp/harbor-transport
chmod 700 /tmp/harbor-transport
export PKEXEC_UID=1000
repo=/mnt/share/Workstations
/tmp/harbor-transport ingest-file --repo "$repo" --machine Galactica --name home-1 --file /mnt/share/payload.bin --experimental --allow-local > /mnt/share/galactica.json
test "$(jq -r '.new_objects' /mnt/share/galactica.json)" -eq 0
test "$(jq -r '.reused_objects' /mnt/share/galactica.json)" -gt 0
test -f "$repo/machines/Galactica/manifests/home-1.json"
test ! -e "$repo/machines/Galactica/objects"
/tmp/harbor-transport recover-file --repo "$repo" --name m@Galactica@home-1 --output /mnt/share/galactica-restored.bin >/mnt/share/restore.json
cmp /mnt/share/payload.bin /mnt/share/galactica-restored.bin
/tmp/harbor-transport ingest-file --repo "$repo" --machine Pegasus --name root-2 --file /mnt/share/payload-modified.bin --experimental --allow-local > /mnt/share/pegasus-update.json
test "$(jq -r '.reused_objects' /mnt/share/pegasus-update.json)" -gt 0
# 9p has no certified multi-client GC lock contract; fail closed.
 /tmp/harbor-transport prune --repo "$repo" --name m@Pegasus@root-1 --name m@Pegasus@root-2 > /mnt/share/remote-plan.json
token="$(jq -r '.plan.plan_sha256' /mnt/share/remote-plan.json)"
if /tmp/harbor-transport prune --repo "$repo" --name m@Pegasus@root-1 --name m@Pegasus@root-2 --confirm-plan "$token"; then
    echo REMOTE_GC_MUST_BE_REJECTED
    exit 40
fi
test -f "$repo/machines/Pegasus/manifests/root-1.json"
# Test local Btrfs GC using a copied fixture on a disposable virtual disk.
mkfs.btrfs -fq /dev/vda
mkdir -p /mnt/btrfs
mount -t btrfs /dev/vda /mnt/btrfs
chown 1000:1000 /mnt/btrfs
cp -a "$repo" /mnt/btrfs/Workstations
localrepo=/mnt/btrfs/Workstations
chown -R 1000:1000 "$localrepo"
/tmp/harbor-transport verify --repo "$localrepo" --name m@Galactica@home-1
/tmp/harbor-transport prune --repo "$localrepo" --name m@Pegasus@root-1 --name m@Pegasus@root-2 > /mnt/share/local-plan.json
localtoken="$(jq -r '.plan.plan_sha256' /mnt/share/local-plan.json)"
/tmp/harbor-transport prune --repo "$localrepo" --name m@Pegasus@root-1 --name m@Pegasus@root-2 --confirm-plan "$localtoken" > /mnt/share/local-gc.json
test ! -e "$localrepo/machines/Pegasus/manifests/root-1.json"
test -f "$localrepo/machines/Galactica/manifests/home-1.json"
/tmp/harbor-transport verify --repo "$localrepo" --name m@Galactica@home-1
/tmp/harbor-transport recover-file --repo "$localrepo" --name m@Galactica@home-1 --output /mnt/btrfs/recovered.bin > /mnt/share/local-restore.json
cmp /mnt/share/payload.bin /mnt/btrfs/recovered.bin
echo GALACTICA_SECOND_GUEST_GC_RESTORE_SUCCESS
"""

def guest(name: str, work: Path, share: Path, iso: Path, proof: Path) -> None:
    disk = work / (name + ".raw")
    subprocess.run(["truncate", "-s", "768M", str(disk)], check=True)
    args = ["-machine", "q35,accel=tcg", "-cpu", "max",
            "-m", "768", "-smp", "2",
            "-kernel", str(work / "vmlinuz-virt"),
            "-initrd", str(work / "initramfs-virt"),
            "-append", "console=ttyS0,115200 alpine_dev=sr0",
            "-cdrom", str(iso),
            "-drive", "file=" + str(disk) + ",format=raw,if=virtio",
            "-virtfs", "local,path=" + str(share) + ",security_model=none,mount_tag=hostshare,id=host0",
            "-netdev", "user,id=n0", "-device", "virtio-net-pci,netdev=n0",
            "-display", "none", "-serial", "stdio", "-monitor", "none", "-no-reboot"]
    log_path = proof / (name + "-qemu.log")
    with log_path.open("wb") as logfile:
        child = pexpect.spawn("qemu-system-x86_64", args, encoding=None, timeout=180)
        child.logfile = logfile
        try:
            child.expect(b"localhost login:", timeout=180)
            child.sendline(b"root")
            child.expect(b"localhost:~#", timeout=50)
            child.sendline(b"stty -echo")
            child.expect(b"localhost:~#", timeout=15)
            child.sendline(b"ip link set eth0 up; udhcpc -i eth0 -q; echo https://dl-cdn.alpinelinux.org/alpine/v3.23/main > /etc/apk/repositories; apk add --no-cache btrfs-progs coreutils jq >/tmp/apk.log; mkdir -p /mnt/share; mount -t 9p -o trans=virtio,version=9p2000.L hostshare /mnt/share; echo __READY__")
            child.expect(b"__READY__", timeout=180)
            child.expect(b"localhost:~#", timeout=20)
            marker = ("__" + name.upper() + "_COMPLETE__").encode()
            child.sendline(("sh /mnt/share/" + name + ".sh && echo " + marker.decode()).encode())
            child.expect(marker, timeout=420)
            child.expect(b"localhost:~#", timeout=20)
            child.sendline(b"poweroff")
            child.expect(pexpect.EOF, timeout=60)
        finally:
            if child.isalive():
                child.terminate(force=True)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--iso", type=Path, required=True)
    parser.add_argument("--temp-root", type=Path, required=True)
    args = parser.parse_args()
    assert args.iso.is_file() and args.binary.is_file()
    assert hashlib.sha256(args.iso.read_bytes()).hexdigest() == ISO_SHA256, "Unpinned Alpine ISO"
    args.temp_root.mkdir(parents=True, exist_ok=True)
    proof = args.temp_root
    with tempfile.TemporaryDirectory(prefix="r45-two-guest-", dir=proof) as td:
        work = Path(td)
        subprocess.run(["7z", "e", "-y", "-o" + str(work), str(args.iso),
                        "boot/vmlinuz-virt", "boot/initramfs-virt"],
                       check=True, stdout=subprocess.DEVNULL)
        share = work / "shared"
        share.mkdir()
        shutil.copy2(args.binary, share / "harbor-transport")
        root = share / "Workstations"
        root.mkdir()
        data = random.Random(20261021).randbytes(12 * 1024 * 1024)
        (share / "payload.bin").write_bytes(data)
        (share / "payload-modified.bin").write_bytes(b"incremental-prefix-2026" + data)
        (share / "pegasus.sh").write_text(PEGASUS)
        (share / "galactica.sh").write_text(GALACTICA)
        guest("pegasus", work, share, args.iso, proof)
        guest("galactica", work, share, args.iso, proof)
        stats = {name: json.loads((share / name).read_text())
                 for name in ("pegasus.json", "galactica.json", "pegasus-update.json",
                              "local-gc.json", "local-plan.json", "remote-plan.json")}
        assert stats["galactica.json"]["new_objects"] == 0
        assert stats["galactica.json"]["reused_objects"] > 0
        assert stats["pegasus-update.json"]["reused_objects"] > 0
        assert hashlib.sha256((share / "galactica-restored.bin").read_bytes()).digest() == hashlib.sha256(data).digest()
        result = {
            "status": "PASS_TWO_SEPARATE_LINUX_QEMU_GUESTS",
            "new_pegasus": stats["pegasus.json"]["new_objects"],
            "new_galactica": stats["galactica.json"]["new_objects"],
            "reused_galactica": stats["galactica.json"]["reused_objects"],
            "reused_incremental_pegasus": stats["pegasus-update.json"]["reused_objects"],
            "reclaimable_objects": stats["local-plan.json"]["plan"]["orphan_objects"],
            "source_sha256": hashlib.sha256(data).hexdigest(),
            "restored_sha256": hashlib.sha256((share / "galactica-restored.bin").read_bytes()).hexdigest(),
            "static_binary_sha256": hashlib.sha256(args.binary.read_bytes()).hexdigest(),
            "scope": "two isolated Linux guests, NOT physical Pegasus or macOS Galactica",
        }
        (proof / "R45_results.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
