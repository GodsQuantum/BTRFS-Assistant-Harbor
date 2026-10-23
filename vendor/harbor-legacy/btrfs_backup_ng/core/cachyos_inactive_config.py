"""Apply fresh-install identity to an INACTIVE restored CachyOS root.

This changes only files under a verified new @harbor-<set>-root subvolume,
NEVER the active system, /boot ESP, NVRAM, LUKS or mount configuration.
It is a preparation stage, not a bootloader activation/certification.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import stat
import uuid

from .cachyos_activation_plan import ActivationPlan

_HOST = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,62}$")
_ROOT = re.compile(r"^@harbor-[0-9a-f]{8}-root$")
_LIMINE_DEFAULT = re.compile(
    r'(?m)^[ \t]*KERNEL_CMDLINE\[default\](?:\+?=)"[^"\r\n]*"[ \t]*$'
)
_OTHER_LIMINE = re.compile(r'(?m)^[ \t]*KERNEL_CMDLINE\[(?!default\])[^\n]*$')
_CMD_SAFE = re.compile(r"^[A-Za-z0-9_.,=/:@+%\- \t]+$")


def planned_limine_config(fresh_config: str, kernel_cmdline: str) -> str:
    """Use a new disk's native Limine defaults, never the old Pegasus UUID."""
    if len(fresh_config) > 256 * 1024 or not _CMD_SAFE.fullmatch(kernel_cmdline):
        raise ValueError("unsafe native Limine config or kernel command")
    if "\x00" in fresh_config or len(_LIMINE_DEFAULT.findall(fresh_config)) != 1:
        raise ValueError("expected exactly one simple Limine default cmdline")
    if _OTHER_LIMINE.search(fresh_config):
        # Kernel-specific overrides could silently use the ORIGINAL disk UUID.
        raise ValueError("kernel-specific Limine command overrides require review")
    return _LIMINE_DEFAULT.sub(
        lambda _: 'KERNEL_CMDLINE[default]="' + kernel_cmdline + '"',
        fresh_config,
    )


def _atomic_replace_existing(etc_fd: int, leaf: str, contents: bytes) -> None:
    """Replace one known existing config as root, with no symlink traversal."""
    if leaf not in {"fstab", "hostname", "machine-id", "crypttab"}:
        raise ValueError("file not allowlisted for inactive root config")
    try:
        st = os.stat(leaf, dir_fd=etc_fd, follow_symlinks=False)
    except FileNotFoundError:
        if leaf != "crypttab":
            raise ValueError("missing expected fresh-target config: " + leaf) from None
        st = None
    if st is not None and (
            not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or
            st.st_size > 512 * 1024 or st.st_mode & 0o022):
        raise ValueError("unsafe existing target config: " + leaf)
    name = ".harbor-pending-" + uuid.uuid4().hex
    fd = os.open(name, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600,
                 dir_fd=etc_fd)
    try:
        if st is not None:
            os.fchown(fd, st.st_uid, st.st_gid)
            os.fchmod(fd, stat.S_IMODE(st.st_mode))
        else:
            os.fchmod(fd, 0o600)
        if os.write(fd, contents) != len(contents):
            raise OSError("incomplete restored config write")
        os.fsync(fd)
    finally:
        os.close(fd)
    try:
        os.rename(name, leaf, src_dir_fd=etc_fd, dst_dir_fd=etc_fd)
        os.fsync(etc_fd)
    except Exception:
        os.unlink(name, dir_fd=etc_fd)
        raise


def configure_inactive_root(
    plan: ActivationPlan,
    inactive_root: Path,
    *,
    fresh_crypttab: str,
    fresh_limine_config: str,
) -> dict:
    """Materialize selected *inactive* root identity only. ESP remains intact."""
    if os.geteuid() != 0:
        raise PermissionError("root needed for a recovered Btrfs subvolume")
    if plan.bootable_certified or not plan.requires_offline_activation:
        raise ValueError("unexpected boot certification")
    if not _HOST.fullmatch(plan.target_hostname) or not re.fullmatch(
            r"[0-9a-f]{32}", plan.fresh_machine_id):
        raise ValueError("unsafe target hostname/machine-id")
    if (not inactive_root.is_absolute() or inactive_root.is_symlink()
            or not _ROOT.fullmatch(inactive_root.name)
            or not inactive_root.is_dir() or inactive_root == Path("/")
            or inactive_root.is_mount()):
        raise ValueError("not a safe inactive restored Btrfs root")
    if inactive_root.name != "@harbor-" + plan.set_id[:8] + "-root":
        raise ValueError("restored root does not match selected backup date")
    if ("\x00" in fresh_crypttab or len(fresh_crypttab) > 128 * 1024
            or "\n" in plan.target_hostname or len(plan.fstab) > 512 * 1024):
        raise ValueError("invalid fresh encryption or filesystem config")
    # Current bootloader settings belong to the *fresh installation*. This
    # prepares what the eventual offline chroot would use; no Limine invocation.
    updated_limine = planned_limine_config(
        fresh_limine_config, plan.limine_cmdline)
    # The native config must already exist on the recovered root and be
    # replaced by an atomic /etc/default file transaction, without touching ESP.
    etc = inactive_root / "etc"
    default = etc / "default"
    if etc.is_symlink() or default.is_symlink() or not default.is_dir():
        raise ValueError("unsafe restored /etc/default")
    etc_fd = os.open(etc, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    default_fd = os.open(default, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        if not stat.S_ISDIR(os.fstat(etc_fd).st_mode):
            raise ValueError("missing restored /etc")
        # Preflight ALL known existing config entries before any overwrite,
        # so a symlink attack on the last file cannot leave early files changed.
        for leaf in ("fstab", "hostname", "machine-id"):
            st = os.stat(leaf, dir_fd=etc_fd, follow_symlinks=False)
            if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or st.st_mode & 0o022:
                raise ValueError("invalid restored /etc/" + leaf)
        limine = os.stat("limine", dir_fd=default_fd, follow_symlinks=False)
        if not stat.S_ISREG(limine.st_mode) or limine.st_nlink != 1 or limine.st_mode & 0o022:
            raise ValueError("invalid restored Limine defaults")
        for leaf, value in (
            ("fstab", plan.fstab + "" if plan.fstab.endswith("\n") else plan.fstab + "\n"),
            ("hostname", plan.target_hostname + "\n"),
            ("machine-id", plan.fresh_machine_id + "\n"),
            ("crypttab", fresh_crypttab),
        ):
            _atomic_replace_existing(etc_fd, leaf, value.encode("utf-8"))
        # This file is under the restored root ONLY, not the active /etc or
        # the real /boot/limine.conf in the FAT32 partition.
        name = ".harbor-limine-" + uuid.uuid4().hex
        fd = os.open(name, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                     0o600, dir_fd=default_fd)
        try:
            os.fchmod(fd, stat.S_IMODE(limine.st_mode))
            text = updated_limine.encode("utf-8")
            if os.write(fd, text) != len(text):
                raise OSError("short Limine config write")
            os.fsync(fd)
        finally:
            os.close(fd)
        os.rename(name, "limine", src_dir_fd=default_fd, dst_dir_fd=default_fd)
        os.fsync(default_fd)
    finally:
        os.close(default_fd)
        os.close(etc_fd)
    return {
        "prepared_root": str(inactive_root),
        "target_hostname": plan.target_hostname,
        "kept_fresh_machine_id": True,
        "bootloader": "limine",
        "bootloader_invoked": False,
        "bootable_certified": False,
    }
