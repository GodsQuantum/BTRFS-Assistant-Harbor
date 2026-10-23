"""Linux overmount selection regression: the top visible mount is authoritative."""

import unittest
from pathlib import Path

from btrfs_backup_ng.endpoint.mount_guard_v2 import _find_mount, parse_mountinfo


class MountStackingTest(unittest.TestCase):
    def test_last_overmount_wins_at_same_mountpoint(self):
        text = (
            "40 20 8:1 / / rw - ext4 /dev/sda1 rw\n"
            "41 40 8:1 /boot /boot rw - ext4 /dev/sda1 rw\n"
            "53 40 7:7 / /boot rw - vfat /dev/loop7 rw\n"
        )
        selected = _find_mount(Path("/boot"), parse_mountinfo(text))
        self.assertEqual(selected.mount_id, 53)
        self.assertEqual(selected.dev, "7:7")
        self.assertEqual(selected.fstype, "vfat")

    def test_longer_mount_path_wins_over_later_parent(self):
        text = (
            "40 20 8:1 / / rw - ext4 /dev/sda1 rw\n"
            "41 40 7:1 / /boot rw - vfat /dev/loop1 rw\n"
            "42 40 8:1 / / rw - ext4 /dev/sda1 rw\n"
            "43 41 7:2 / /boot/efi rw - vfat /dev/loop2 rw\n"
        )
        selected = _find_mount(Path("/boot/efi/EFI"), parse_mountinfo(text))
        self.assertEqual(selected.mount_id, 43)


if __name__ == "__main__":
    unittest.main()
