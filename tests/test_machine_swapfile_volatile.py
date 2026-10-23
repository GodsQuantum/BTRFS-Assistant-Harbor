"""Safely exclude ONLY swap-only Btrfs subvolumes without deactivating swap."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from btrfs_backup_ng.cli.machine_set_v2 import _exclude_verified_volatile_swap


class VerifiedVolatileSwapTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.swap = self.root / "swap"
        self.swap.mkdir()
        (self.swap / "swapfile").write_bytes(b"mock-active-swap")
        self.swaps = self.root / "proc_swaps"
        self.fstab = self.root / "fstab"
        self.swaps.write_text(
            "Filename Type Size Used Priority\n"
            + str(self.swap / "swapfile") + " file 33554428 0 10\n"
        )
        self.fstab.write_text(
            str(self.swap / "swapfile") + " none swap defaults,pri=10 0 0\n"
        )

    def candidate(self):
        return _exclude_verified_volatile_swap(
            ["/home", str(self.swap)],
            swaps_path=self.swaps,
            fstab_path=self.fstab,
            swap_mounts=(str(self.swap),),
        )

    def test_active_swapfile_only_is_volatile_and_excluded(self):
        with patch(
            "btrfs_backup_ng.cli.machine_set_v2._is_real_subvolume_root",
            return_value=True,
        ):
            kept, exclusions = self.candidate()
        self.assertEqual(kept, ["/home"])
        self.assertEqual(len(exclusions), 1)
        self.assertEqual(exclusions[0]["reason"], "verified_volatile_swap_only")
        self.assertEqual(exclusions[0]["swapfiles"], [str(self.swap / "swapfile")])
        self.assertIn("Recreate", exclusions[0]["restore"])

    def test_unrecognized_persistent_data_cannot_be_skipped(self):
        (self.swap / "important-config").write_text("keep me")
        with patch(
            "btrfs_backup_ng.cli.machine_set_v2._is_real_subvolume_root",
            return_value=True,
        ):
            kept, exclusions = self.candidate()
        self.assertEqual(kept, ["/home", str(self.swap)])
        self.assertEqual(exclusions, [])

    def test_not_subvolume_root_is_rejected(self):
        with patch(
            "btrfs_backup_ng.cli.machine_set_v2._is_real_subvolume_root",
            return_value=False,
        ):
            with self.assertRaisesRegex(ValueError, "not a Btrfs subvolume root"):
                self.candidate()

    def test_unlisted_file_kept_if_swap_not_active_or_configured(self):
        self.swaps.write_text("Filename Type Size Used Priority\n")
        self.fstab.write_text("")
        with patch(
            "btrfs_backup_ng.cli.machine_set_v2._is_real_subvolume_root",
            return_value=True,
        ):
            kept, exclusions = self.candidate()
        self.assertEqual(kept, ["/home", str(self.swap)])
        self.assertEqual(exclusions, [])


if __name__ == "__main__":
    unittest.main()
