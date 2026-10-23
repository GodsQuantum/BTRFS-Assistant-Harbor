"""Verified, read-only preflight on an installed fresh CachyOS.

This deliberately CANNOT activate a root or change boot files. A future
activation runner must execute only from offline recovery, with an isolated
UEFI/LUKS2/Limine boot test and rollback proof.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import socket
import stat
import subprocess

from .cachyos_activation_plan import plan_cachyos_activation
from .rear_bridge_v2 import find_received_subvolume

_MAX_TEXT = 512 * 1024
_UUID = re.compile(r"^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$")


def _read_verified_text(root: Path, subpath: str, *, cap: int = _MAX_TEXT) -> str:
    """Never follow a staged reference outside the received Btrfs subvolume."""
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise ValueError("invalid received Btrfs root")
    path = root / subpath
    if not path.resolve(strict=True).is_relative_to(root.resolve(strict=True)):
        raise ValueError("staged system file escapes backup root")
    if not path.is_file():
        raise ValueError("missing recovered system file: " + subpath)
    resolved = path.resolve(strict=True)
    fd = os.open(resolved, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > cap:
            raise ValueError("invalid recovered file size or type")
        data = os.read(fd, cap + 1)
        if len(data) > cap:
            raise ValueError("system recovery file too large")
        return data.decode("utf-8")
    finally:
        os.close(fd)


def _mount_filesystem(path: str) -> str:
    proc = subprocess.run(
        ["findmnt", "-rn", "-o", "FSTYPE", "--mountpoint", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        check=False, timeout=10,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _active_root_mapper() -> str:
    result = subprocess.run(
        ["findmnt", "-rn", "-o", "SOURCE", "--mountpoint", "/"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        check=False, timeout=10,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _intent(staging: Path, catalog: dict) -> dict:
    filename = staging / ".harbor-recovery-intent.json"
    if filename.is_symlink() or not filename.is_file():
        raise ValueError("missing committed recovery selection")
    fd = os.open(filename, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        meta = os.fstat(fd)
        if not stat.S_ISREG(meta.st_mode) or meta.st_size > 8192 or meta.st_mode & 0o022:
            raise ValueError("recovery selection file has unsafe type/mode")
        content = os.read(fd, 8193)
        if len(content) > 8192:
            raise ValueError("recovery intent too large")
        selected = json.loads(content)
    finally:
        os.close(fd)
    if not isinstance(selected, dict) or selected.get("version") != 1:
        raise ValueError("invalid recovery selection schema")
    if selected.get("set_id") != catalog["set_id"]:
        raise ValueError("recovery selection and backup do not match")
    if selected.get("source_machine") != catalog.get("machine_name"):
        raise ValueError("wrong source machine in recovery selection")
    if selected.get("boot_activation_certified") is not False:
        raise ValueError("untrusted boot certification bit")
    return selected


def probe_installed_cachyos(catalog: dict, staging: Path) -> dict:
    """No writes anywhere. The running machine is never a restore target."""
    if (os.geteuid() != 0 or not staging.is_absolute() or staging.is_symlink()
            or not staging.is_dir()):
        raise ValueError("privileged, real Btrfs staging path required")
    if _mount_filesystem(str(staging)) != "btrfs" and not (
            subprocess.run(["findmnt", "-n", "-o", "FSTYPE", "-T", str(staging)],
                           capture_output=True, text=True, check=False,
                           timeout=10).stdout.strip() == "btrfs"):
        raise ValueError("staging is not on Btrfs")
    if _mount_filesystem("/") != "btrfs":
        raise ValueError("fresh system root is not mounted on Btrfs")
    if _mount_filesystem("/boot") != "vfat":
        raise ValueError("fresh CachyOS has no separately mounted FAT32 /boot")
    if (not Path("/boot/limine.conf").is_file() or
            not Path("/etc/default/limine").is_file() or
            not shutil.which("limine-mkinitcpio")):
        raise ValueError("fresh CachyOS Limine utilities or config missing")

    selected = _intent(staging, catalog)
    members = catalog.get("members", [])
    matches = [(i, member) for i, member in enumerate(members)
               if member.get("original_mount") == "/"]
    if len(matches) != 1:
        raise ValueError("missing single machine root in dated set")
    index, member = matches[0]
    uuid = member.get("snapshot_uuid")
    if not isinstance(uuid, str) or not _UUID.fullmatch(uuid):
        raise ValueError("invalid received root snapshot UUID")
    restored_root = find_received_subvolume(
        staging / f"volume-{index:03d}", uuid)

    proc_cmdline = Path("/proc/cmdline").read_text(encoding="utf-8")
    plan = plan_cachyos_activation(
        catalog,
        source_os_release=_read_verified_text(restored_root, "etc/os-release"),
        fresh_os_release=Path("/etc/os-release").read_text(encoding="utf-8"),
        source_fstab=_read_verified_text(restored_root, "etc/fstab"),
        fresh_fstab=Path("/etc/fstab").read_text(encoding="utf-8"),
        fresh_limine_cmdline=proc_cmdline,
        fresh_machine_id=Path("/etc/machine-id").read_text(encoding="utf-8").strip(),
        current_hostname=socket.gethostname(),
        hostname_policy=selected.get("hostname_policy", ""),
        custom_hostname=selected.get("target_hostname", ""),
    )
    if selected["target_hostname"] != plan.target_hostname:
        raise ValueError("hostname policy and committed selected name disagree")
    match = re.search(r"(?:^|\s)rd\.luks\.uuid=([0-9a-f-]{36})(?:\s|$)",
                      plan.limine_cmdline)
    if match is None:
        raise ValueError("cannot certify fresh encrypted root")
    source = _active_root_mapper()
    fresh_mapping = f"/dev/mapper/luks-{match.group(1)}"
    if source not in (fresh_mapping, fresh_mapping + "[/@]"):
        raise ValueError("booted root is not the expected fresh LUKS mapper")
    return {
        "dry_run": True,
        "set_id": plan.set_id,
        "source_machine": plan.source_hostname,
        "target_hostname": plan.target_hostname,
        "volumes": len(plan.mounts),
        "target_subvolumes": dict(plan.mounts),
        "preserve_fresh_machine_id": True,
        "preserve_fresh_luks_uuid_and_passphrase": True,
        "filesystem": "btrfs",
        "esp": "vfat:/boot",
        "bootloader": plan.bootloader,
        "activation_performed": False,
        "bootable_certified": False,
        "blocker": "CachyOS offline activation and UEFI/LUKS2/Limine boot proof not implemented",
    }
