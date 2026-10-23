#!/usr/bin/env python3
"""Boot official CachyOS restored disk via OVMF/Limine, never ISO.

Only the HARBOR_CACHYOS_RESTORED_UEFI_LUKS2_BOOT_OK serial proof is a
success. QEMU process creation, EFI menu screenshots, root password prompt,
or source-root boot are NOT sufficient evidence for recovery certification.
"""
from __future__ import annotations
import os
from pathlib import Path
import sys
import time

import pexpect

PASSMARK = "HARBOR_CACHYOS_RESTORED_UEFI_LUKS2_BOOT_OK"
PASS_PHRASE = "harbor-ci-only-test-passphrase"


def main() -> None:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("QEMU boot proof is restricted to disposable CI")
    if len(sys.argv) != 4:
        raise SystemExit("usage: qa_cachyos_uefi_guest_expect.py RAW_DISK OVMF_VARS LOG")
    disk, vars_image, log = (Path(x) for x in sys.argv[1:4])
    if not disk.is_file() or not vars_image.is_file():
        raise ValueError("missing freshly installed VM disk or firmware variables")
    code = Path("/usr/share/OVMF/OVMF_CODE.fd")
    if not code.is_file():
        raise ValueError("OVMF_CODE.fd not installed")
    cmd = [
        "qemu-system-x86_64",
        "-machine", "q35,accel=tcg",
        "-cpu", "max",
        "-smp", "2",
        "-m", "3072",
        "-drive", f"if=pflash,format=raw,readonly=on,file={code}",
        "-drive", f"if=pflash,format=raw,file={vars_image}",
        "-drive", f"if=virtio,format=raw,file={disk}",
        "-display", "none",
        "-serial", "stdio",
        "-monitor", "none",
        "-no-reboot",
        "-net", "none",
    ]
    deadline = time.monotonic() + 900
    with log.open("wb") as stream:
        child = pexpect.spawn(cmd[0], cmd[1:], encoding=None, timeout=90)
        child.logfile = stream
        try:
            unlocked = 0
            while time.monotonic() < deadline:
                which = child.expect([
                    PASSMARK.encode(),
                    b"(?i)(passphrase for|enter passphrase|password for|please unlock)",
                    b"(?i)(kernel panic|unable to mount root|emergency mode)",
                    pexpect.EOF,
                    pexpect.TIMEOUT,
                ], timeout=90)
                if which == 0:
                    print(PASSMARK)
                    return
                if which == 1:
                    if unlocked >= 4:
                        raise AssertionError("encrypted root did not unlock after retries")
                    child.sendline(PASS_PHRASE.encode("ascii"))
                    unlocked += 1
                    print("HARBOR_VM_CRYPTSETUP_PASSPHRASE_SUBMITTED")
                elif which == 2:
                    raise AssertionError("restored CachyOS kernel panicked or entered emergency mode")
                elif which == 3:
                    raise AssertionError("restored CachyOS VM shut down without proof")
            raise AssertionError("QEMU timeout without restored-root proof")
        finally:
            if child.isalive():
                child.terminate(force=True)


if __name__ == "__main__":
    main()
