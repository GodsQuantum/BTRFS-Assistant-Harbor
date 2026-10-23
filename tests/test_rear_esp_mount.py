"""CachyOS /boot can itself be the VFAT EFI system partition."""
import unittest
from btrfs_backup_ng.core.rear_iso_v2 import _check_catalog


class CachyosEspRecovery(unittest.TestCase):
    def complete(self, mount):
        return {
            "status": "completed_btrfs_and_boot_files",
            "members": [{"original_mount": "/", "status": "completed"}],
            "boot_members": [{"mount_point": mount, "filesystem": "vfat",
                              "status": "completed"}],
        }

    def test_root_boot_efi_vfat_layout_supported(self):
        _check_catalog(self.complete("/boot"))

    def test_nested_efi_layout_supported(self):
        _check_catalog(self.complete("/boot/efi"))

    def test_non_efi_mount_rejected(self):
        with self.assertRaises(ValueError):
            _check_catalog(self.complete("/home"))

    def test_incomplete_set_rejected(self):
        record = self.complete("/boot")
        record["status"] = "pending"
        with self.assertRaises(ValueError):
            _check_catalog(record)


if __name__ == "__main__":
    unittest.main()
