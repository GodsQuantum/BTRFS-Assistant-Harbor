"""Real native EFI+multi-Btrfs backup/receive in isolated CI mount namespace.

Only source enumeration is injected for this disposable fixture. The native
mount identity guard, FAT32 tar archive, hash verifier, transfer engine, and
Btrfs receiver are exercised unchanged. Never run on a real workstation.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

from btrfs_backup_ng.cli import machine_set_v2 as mset
from btrfs_backup_ng.core.boot_files_v2 import verify_boot_member


def main() -> None:
    if os.geteuid() != 0 or os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("disposable root CI runner only")
    if len(sys.argv) != 5:
        raise SystemExit("usage: qa_full_machine_efi_fixture.py REPO ROOT HOME STAGING")
    repo, root, home, staging = map(Path, sys.argv[1:5])
    assert not repo.exists() or not any(repo.iterdir())
    repo.mkdir(parents=True, exist_ok=True)
    staging.mkdir(parents=True, exist_ok=True)
    if not Path("/boot/vmlinuz-linux-cachyos").is_file():
        raise AssertionError("isolated /boot is not the test FAT32 ESP")
    args = argparse.Namespace(
        checkpoint_action="set-start",
        target=str(repo),
        profile_id="118e0b70-dced-4a95-9179-8b45efbd3f51",
        source=None,
        snapshot_provider="harbor",
        max_incremental_depth=7,
        allow_local=True,
        experimental=True,
        state_dir=None,
    )
    # The runner's preexisting /boot (often ext4) stays safely mounted
    # BELOW our disposable FAT32 bind mount within the private namespace.
    # The test injects the topmost /boot mount row, but the native actual
    # capture_mount_identity and boot verifier remain UNPATCHED.
    original_rows = mset._mount_rows

    def fixture_mount_rows(content: str):
        rows = original_rows(content)
        boot_rows = [row for row in rows if row["mount_point"] == "/boot"]
        assert boot_rows and boot_rows[-1]["filesystem"] == "vfat", boot_rows
        return [row for row in rows if row["mount_point"] != "/boot"] + [boot_rows[-1]]

    # Publish precise mount diagnostics for CI without relaxing any production
    # filesystem guards; runner /boot layouts differ between Ubuntu images.
    boot_path = Path("/boot")
    print(
        "HARBOR_CI_BOOT_DIAGNOSTIC",
        "is_dir=", boot_path.is_dir(),
        "is_symlink=", boot_path.is_symlink(),
        "realpath=", os.path.realpath("/boot"),
        "file_present=", (boot_path / "vmlinuz-linux-cachyos").is_file(),
        flush=True,
    )
    # ONLY the fixture source enumeration and the isolated runner's stacked
    # mount-row representation are patched, not the production boot archivist.
    with patch.object(
        mset, "_sources_from_inventory", return_value=([str(root), str(home)], None)
    ), patch.object(mset, "_mount_rows", side_effect=fixture_mount_rows):
        assert mset.execute_machine_set(args) == 0
    records = list(repo.glob(".harbor-machine-set-*.json"))
    assert len(records) == 1, records
    data = json.loads(records[0].read_text())
    assert data["status"] == "completed_btrfs_and_boot_files", data["status"]
    assert data["coverage"] == "btrfs-and-boot-files"
    assert len(data["members"]) == 2
    assert len(data["boot_members"]) == 1
    efi = data["boot_members"][0]
    assert efi["mount_point"] == "/boot", efi
    assert efi["filesystem"] == "vfat", efi
    assert efi["status"] == "completed", efi
    assert verify_boot_member(repo, efi)
    print("PASS_NATIVE_FULL_MACHINE_BTRFS_AND_REAL_VFAT_ESP_ARCHIVE")

    restore = argparse.Namespace(
        checkpoint_action="set-restore",
        target=str(repo),
        set_id=data["set_id"],
        staging=str(staging),
        allow_local=True,
        experimental=True,
        confirm=True,
        state_dir=None,
    )
    assert mset.execute_machine_set(restore) == 0
    restored = staging / "boot-files" / "boot-000"
    assert (restored / "vmlinuz-linux-cachyos").read_bytes() == (
        Path("/boot/vmlinuz-linux-cachyos").read_bytes()
    )
    assert (restored / "initramfs-linux-cachyos.img").read_bytes() == (
        Path("/boot/initramfs-linux-cachyos.img").read_bytes()
    )
    assert (restored / "limine.conf").read_bytes() == Path("/boot/limine.conf").read_bytes()
    print("PASS_NATIVE_WHOLE_MACHINE_EFI_AND_BTRFS_VERIFIED_RESTORE")
    # This is an archive and staged recovery proof, not a full UEFI boot.
    assert data["bootable"] is False


if __name__ == "__main__":
    main()
