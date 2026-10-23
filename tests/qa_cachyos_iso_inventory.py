"""Parse pinned official CachyOS ISO members before building real UEFI boot VM.

Inventory only. Does NOT claim fresh-install boot certification.
"""
from __future__ import annotations
import json
from pathlib import Path
import re
import sys

if __name__ == "__main__":
    entries = []
    for line in Path(sys.argv[1]).read_text(errors="replace").splitlines():
        if line.startswith("Path = "):
            entries.append(line.partition(" = ")[2])
    filtered = {
        "installer_kernels": [p for p in entries if re.search(
            r"(^|/)(vmlinuz|vmlinu[xz])[-.][A-Za-z0-9._-]+$", p,
            re.IGNORECASE,
        )],
        "initramfs": [p for p in entries if re.search(
            r"(^|/)(initramfs|initrd)[-_A-Za-z0-9.]+$", p,
            re.IGNORECASE,
        )],
        "squashfs": [p for p in entries if p.endswith((".sfs", ".squashfs"))],
        "limine": [p for p in entries if "limine" in p.lower() and p.lower().endswith(
            (".efi", ".conf", ".cfg")
        )],
        "member_count": len(entries),
        "boot_certified": False,
    }
    if not entries or not filtered["squashfs"]:
        raise SystemExit("unexpected CachyOS ISO: missing filesystem payload")
    Path(sys.argv[2]).write_text(json.dumps(filtered, indent=2) + "\n")
