#!/usr/bin/env python3
"""UEFI+GPT+Btrfs Alpine system-disk installation/boot in disposable QEMU.

Phase 1: prove a GPT/ESP/Btrfs disk can boot via OVMF without rescue ISO.
This does not claim a successful *restoration* yet; ReaR remains a separate gate.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import pexpect

EXPECTED_ISO_SHA256 = "d91fb5c7a73528c89e0a1aa9a7d959f9deb9ca3dc5211e39bd73fd7df0d9070e"
INSTALL = r"""#!/bin/sh
set -eu
test -b /dev/vda
test ! -b /dev/vdb
test -d /sys/firmware/efi
ip link set eth0 up
udhcpc -i eth0 -q
echo https://dl-cdn.alpinelinux.org/alpine/v3.23/main > /etc/apk/repositories
apk add --no-cache btrfs-progs dosfstools grub-efi util-linux e2fsprogs >/mnt/share/apk-install.log 2>&1 || { cat /mnt/share/apk-install.log; exit 21; }
export USE_EFI=1 ROOTFS=btrfs DISKLABEL=gpt BOOTFS=vfat
export BOOTLOADER=grub KERNELOPTS="console=ttyS0,115200 rootfstype=btrfs modules=sd-mod,virtio_blk,btrfs"
export ERASE_DISKS=/dev/vda
setup-disk -m sys -k virt -s 0 /dev/vda > /mnt/share/setup-disk.log 2>&1 || { tail -70 /mnt/share/setup-disk.log; exit 22; }
blkid /dev/vda1 /dev/vda2 > /mnt/share/installed-blkid.log
test -b /dev/vda1
test -b /dev/vda2
blkid /dev/vda1 | grep -Eq '(vfat|TYPE="vfat")'
blkid /dev/vda2 | grep -Eq '(btrfs|TYPE="btrfs")'
# Alpine setup-disk has previously returned 0 on an unsupported bootloader
# name. The ESP executable, not just the installer exit status, is essential.
! grep -Eqi 'bootloader.*not supported|grub.*error' /mnt/share/setup-disk.log
mkdir -p /mnt/efi-check
mount -t vfat /dev/vda1 /mnt/efi-check
test -s /mnt/efi-check/EFI/boot/bootx64.efi || { echo EFI_FALLBACK_MISSING; exit 25; }
umount /mnt/efi-check
echo HARBOR_ALPINE_UEFI_BTRFS_DISK_INSTALLED
"""

def run_guest(args: list[str], logfile: Path) -> pexpect.spawn:
    f=logfile.open("wb")
    child=pexpect.spawn("qemu-system-x86_64",args,encoding=None,timeout=260)
    child.logfile=f
    child._harbor_logfile=f
    return child

def terminate(child: pexpect.spawn) -> None:
    if child.isalive():
        child.terminate(force=True)
    child._harbor_logfile.close()

def main() -> None:
    parser=argparse.ArgumentParser()
    for key in ("iso","ovmf-code","ovmf-vars","scratch"):
        parser.add_argument("--"+key,type=Path,required=True)
    args=parser.parse_args()
    if hashlib.sha256(args.iso.read_bytes()).hexdigest()!=EXPECTED_ISO_SHA256:
        raise ValueError("ISO SHA256 mismatch")
    if not args.scratch.is_dir() or args.scratch.is_symlink():
        raise ValueError("scratch must be existing real directory")
    with tempfile.TemporaryDirectory(prefix=".harbor-uefi-system-disk-",dir=args.scratch) as temp:
        work=Path(temp)
        disk=work/"original-system.raw"
        subprocess.run(["truncate","-s","3072M",str(disk)],check=True)
        vars_file=work/"vars.fd"
        shutil.copyfile(args.ovmf_vars,vars_file)
        share=work/"share"
        share.mkdir()
        (share/"install.sh").write_text(INSTALL)
        base=[
            "-machine","q35,accel=tcg","-cpu","qemu64","-m","1024","-smp","2",
            "-drive",f"if=pflash,format=raw,unit=0,readonly=on,file={args.ovmf_code}",
            "-drive",f"if=pflash,format=raw,unit=1,file={vars_file}",
            "-drive",f"file={disk},format=raw,if=virtio",
            "-serial","stdio","-display","none","-monitor","none","-no-reboot",
        ]
        installer_args=base+["-cdrom",str(args.iso),"-boot","order=d",
            "-virtfs",f"local,path={share},security_model=none,mount_tag=hostshare,id=host0",
            "-netdev","user,id=n0","-device","virtio-net-pci,netdev=n0"]
        child=None
        try:
            child=run_guest(installer_args,work/"install-console.log")
            child.expect(b"localhost login:",timeout=230)
            child.sendline(b"root")
            child.expect(b"localhost:~#",timeout=30)
            child.sendline(b"mkdir -p /mnt/share && mount -t 9p -o trans=virtio,version=9p2000.L hostshare /mnt/share && echo SHARE_READY")
            child.expect(b"SHARE_READY",timeout=30)
            child.expect(b"localhost:~#",timeout=30)
            child.sendline(b"stty -echo")
            child.expect(b"localhost:~#",timeout=20)
            child.sendline(b"sh /mnt/share/install.sh; rc=$?; printf '\\n__HARBOR_INSTALL_RC:%d__\\n' \"$rc\"")
            # Require the standalone completion line, NOT the echoed command
            # that contains the marker before setup-disk has completed.
            outcome = child.expect(
                [rb"\r+\n__HARBOR_INSTALL_RC:0__\r*\n",
                 rb"\r+\n__HARBOR_INSTALL_RC:[1-9][0-9]*__\r*\n"],
                timeout=540,
            )
            if outcome != 0:
                raise RuntimeError("Alpine setup-disk failed in disposable guest")
            child.expect(b"localhost:~#",timeout=40)
            print("PASS GPT ESP FAT32 BTRFS ROOT INSTALLED IN VIRTUAL DISK",flush=True)
            child.sendline(b"poweroff")
            child.expect(pexpect.EOF,timeout=80)
            terminate(child)
            child=None
            boot_args=base+["-boot","order=c","-net","none"]
            child=run_guest(boot_args,work/"boot-console.log")
            child.expect(b"login:",timeout=240)
            print("PASS GPT+ESP SYSTEM DISK BOOTED VIA OVMF (ISO DETACHED)",flush=True)
            child.sendline(b"root")
            child.expect(b"#",timeout=50)
            child.sendline(b"test -d /sys/firmware/efi && findmnt -n -o FSTYPE / | grep -q btrfs && echo EFI_BTRFS_ROOT_VERIFIED")
            child.expect(b"EFI_BTRFS_ROOT_VERIFIED",timeout=30)
            print("PASS OVMF SYSTEM DISK UEFI+BTRFS ROOT VERIFIED",flush=True)
            child.sendline(b"poweroff")
            child.expect(pexpect.EOF,timeout=80)
        except BaseException:
            for filename in ("install-console.log","boot-console.log"):
                file=work/filename
                if file.exists():
                    print(filename,file.read_bytes()[-4200:].decode("utf8","replace"),flush=True)
            for filename in ("setup-disk.log","apk-install.log","installed-blkid.log"):
                file=share/filename
                if file.exists():
                    print(filename,file.read_text(errors="replace")[-2600:],flush=True)
            raise
        finally:
            if child:
                terminate(child)

if __name__ == "__main__":
    main()
