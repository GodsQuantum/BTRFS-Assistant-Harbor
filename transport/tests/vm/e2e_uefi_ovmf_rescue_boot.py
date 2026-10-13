#!/usr/bin/env python3
"""Isolated OVMF UEFI boot smoke test. Not a full machine recovery certificate.

Uses a copy of firmware VARS and an unmodified Alpine ISO. No host EFI access,
no host mounts, no production disks, no GPU virtualization.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import shutil
import tempfile
import pexpect

EXPECTED_ISO_SHA256 = "d91fb5c7a73528c89e0a1aa9a7d959f9deb9ca3dc5211e39bd73fd7df0d9070e"

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--iso",type=Path,required=True)
    parser.add_argument("--ovmf-code",type=Path,required=True)
    parser.add_argument("--ovmf-vars",type=Path,required=True)
    parser.add_argument("--scratch",type=Path,required=True)
    args=parser.parse_args()
    if hashlib.sha256(args.iso.read_bytes()).hexdigest() != EXPECTED_ISO_SHA256:
        raise ValueError("Alpine ISO sha256 mismatch")
    for path in (args.ovmf_code,args.ovmf_vars):
        if not path.is_file() or path.is_symlink():
            raise ValueError("firmware must be a real regular file")
    with tempfile.TemporaryDirectory(prefix=".harbor-ovmf-rescue-qa-",dir=args.scratch) as tmp:
        vars_copy=Path(tmp)/"guest-uefi-vars.fd"
        shutil.copyfile(args.ovmf_vars,vars_copy)
        command=[
            "-machine","q35,accel=tcg", "-cpu","qemu64", "-smp","1", "-m","768",
            "-drive",f"if=pflash,format=raw,unit=0,readonly=on,file={args.ovmf_code}",
            "-drive",f"if=pflash,format=raw,unit=1,file={vars_copy}",
            "-cdrom",str(args.iso),"-boot","order=d",
            "-serial","stdio","-display","none","-monitor","none",
            "-no-reboot","-net","none",
        ]
        with (Path(tmp)/"console.log").open("wb") as logfile:
            child=pexpect.spawn("qemu-system-x86_64",command,encoding=None,timeout=240)
            child.logfile=logfile
            try:
                child.expect(b"localhost login:",timeout=240)
                print("PASS OVMF UEFI ALPINE RESCUE ISO BOOTED TO LOGIN",flush=True)
                child.sendline(b"root")
                child.expect(b"localhost:~#",timeout=45)
                child.sendline(b"test -d /sys/firmware/efi && echo EFI_RUNTIME_PRESENT")
                child.expect(b"EFI_RUNTIME_PRESENT",timeout=25)
                child.expect(b"localhost:~#",timeout=20)
                print("PASS GUEST RUNNING UNDER UEFI FIRMWARE",flush=True)
                child.sendline(b"poweroff")
                child.expect(pexpect.EOF,timeout=60)
                print("PASS EFI ISO SHUTDOWN; BOOTABLE DISK RESTORE NOT TESTED",flush=True)
            except BaseException:
                logfile.flush()
                print("GUEST CONSOLE:",(Path(tmp)/"console.log").read_bytes()[-4000:].decode("utf-8","replace"),flush=True)
                raise
            finally:
                if child.isalive():
                    child.terminate(force=True)

if __name__ == "__main__":
    main()
