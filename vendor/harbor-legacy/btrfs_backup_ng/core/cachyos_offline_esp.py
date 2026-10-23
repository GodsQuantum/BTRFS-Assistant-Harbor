"""Stage an additive recovery menu on a SEPARATE, disposable/offline FAT32 ESP.

Deliberately never changes the currently selected/default boot entry,
NVRAM, Secure Boot enrollment, LUKS, existing kernels, or any Btrfs subvolume.
Only a verified inactive restored root is eligible; this is not a full
restoration and not callable by the production GUI.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import stat
import subprocess
import uuid

from .cachyos_limine_recovery_entry import LimineBootPreview


def _esp_mounted_at(path: Path) -> bool:
    result = subprocess.run(
        ["findmnt", "-rn", "-o", "FSTYPE,TARGET", "--mountpoint", str(path)],
        check=False, capture_output=True, text=True, timeout=10,
    )
    return result.returncode == 0 and result.stdout.strip() == "vfat " + str(path)




def _validate_boot_assets(esp_mount: Path, menu: str) -> None:
    # A present Limine menu is meaningless if the kernel or initramfs files
    # referenced from the fresh ESP are absent. Verify before any write.
    used = 0
    for raw in menu.splitlines():
        m = re.fullmatch(
            r"  (?:path|kernel_path|module_path): boot\(\):/([A-Za-z0-9._/@:+%-]{1,300})(?:#([0-9a-f]{128}))?",
            raw,
        )
        if raw.startswith(("  path:", "  kernel_path:", "  module_path:")) and not m:
            raise ValueError("unsupported EFI boot image resource or checksum")
        if not m:
            continue
        used += 1
        asset = esp_mount / m.group(1)
        if (asset.is_symlink() or not asset.is_file() or
            not asset.resolve(strict=True).is_relative_to(esp_mount.resolve(strict=True))):
            raise ValueError("missing or unsafe EFI kernel/initramfs")
        fd = os.open(asset, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode) or st.st_size < 4 or st.st_size > 1024**3:
                raise ValueError("unsafe EFI kernel/initramfs size")
            if m.group(2) is not None:
                digest = hashlib.blake2b()
                while True:
                    block = os.read(fd, 1024*1024)
                    if not block:
                        break
                    digest.update(block)
                if digest.hexdigest() != m.group(2):
                    raise ValueError("EFI kernel/initramfs checksum mismatch")
        finally:
            os.close(fd)
    if used < 2 or used != 2*menu.count("  cmdline: "):
        raise ValueError("missing EFI kernel+initramfs per recovery entry")

def stage_additive_limine_entry(
    esp_mount: Path,
    preview: LimineBootPreview,
    *,
    set_id: str,
    secure_boot_state: str = "unknown",
    probe_esp=_esp_mounted_at,
) -> dict:
    """Append a removable backup menu to offline ESP, leaving default intact.

    A saved *.harbor-original-UUID file permits a verifiable rollback,
    but this routine does not automatically select or boot the new entry.
    """
    if os.geteuid() != 0:
        raise PermissionError("offline recovery ESP staging requires root")
    if secure_boot_state != "disabled":
        raise ValueError("Secure Boot checksum enrollment has not been certified")
    if (not esp_mount.is_absolute() or esp_mount.is_symlink() or
            not esp_mount.is_dir() or str(esp_mount) in ("/boot", "/boot/efi", "/")):
        raise ValueError("must use a separately mounted, offline ESP")
    if not probe_esp(esp_mount):
        raise ValueError("not a mounted isolated FAT32 EFI partition")
    if not re.fullmatch(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}", set_id):
        raise ValueError("invalid selected machine backup")
    if (preview.bootable_certified or not preview.existing_configuration_untouched or
            preview.title.strip() == "" or not preview.selected_kernel_ids or
            len(preview.menu_addition) > 65536 or
            preview.menu_addition.count("/+Harbor recovery") != 1):
        raise ValueError("untrusted additive Limine recovery menu")
    if "\x00" in preview.menu_addition or "\r" in preview.menu_addition:
        raise ValueError("malformed boot menu")
    if "/@harbor-" + set_id[:8] + "-root" not in preview.menu_addition:
        raise ValueError("recovery kernel root does not match selected backup")
    _validate_boot_assets(esp_mount, preview.menu_addition)

    root = os.open(esp_mount, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        src = os.open("limine.conf", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=root)
        try:
            info = os.fstat(src)
            if (not stat.S_ISREG(info.st_mode) or info.st_size > 8*1024*1024 or
                    info.st_nlink != 1):
                raise ValueError("unsafe existing native Limine config")
            before = os.read(src, 8*1024*1024+1)
        finally:
            os.close(src)
        try:
            original = before.decode("utf-8")
        except UnicodeDecodeError as err:
            raise ValueError("invalid original Limine config encoding") from err
        if "/+Harbor recovery" in original or not original.endswith("\n"):
            raise ValueError("existing config is not a safely appendable baseline")
        if "default_entry:" not in original:
            raise ValueError("fresh OS has no explicitly configured fallback")
        addition = "\n" + preview.menu_addition
        updated = original + addition
        suffix = set_id[:8]
        backup_name = ".limine.conf.harbor-original-" + suffix
        pending = ".limine.conf.harbor-new-" + uuid.uuid4().hex
        backup_fd = os.open(backup_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                            os.O_NOFOLLOW, 0o600, dir_fd=root)
        try:
            if os.write(backup_fd, before) != len(before):
                raise OSError("short Limine original backup write")
            os.fsync(backup_fd)
        finally:
            os.close(backup_fd)
        next_bytes = updated.encode("utf-8")
        try:
            new_fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                             os.O_NOFOLLOW, 0o600, dir_fd=root)
            try:
                if os.write(new_fd, next_bytes) != len(next_bytes):
                    raise OSError("short Limine recovery menu write")
                os.fsync(new_fd)
            finally:
                os.close(new_fd)
            # Atomic, independent new entry. The original menu and every
            # existing default_entry/kernel path remain byte-for-byte intact.
            os.rename(pending, "limine.conf", src_dir_fd=root, dst_dir_fd=root)
            os.fsync(root)
        except Exception:
            try:
                os.unlink(pending, dir_fd=root)
            except FileNotFoundError:
                pass
            raise
        return {
            "backup_file": str(esp_mount / backup_name),
            "recovery_subvol": "/@harbor-" + suffix + "-root",
            "default_selection_preserved": True,
            "secure_boot_state": secure_boot_state,
            "reboot_performed": False,
            "bootable_certified": False,
        }
    finally:
        os.close(root)
