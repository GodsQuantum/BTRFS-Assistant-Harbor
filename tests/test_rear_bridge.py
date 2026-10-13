"""Pure fail-closed ReaR restore bridge tests, no mounts or disk writes."""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from btrfs_backup_ng.core.rear_bridge_v2 import (
    find_received_subvolume,
    plan_rear_restore,
    reconcile_fstab,
    recorded_uuids,
)

UUID = "a5d970db-9664-4be8-a0fb-bb1e93c60ec3"
ALT = "3554efe8-75e3-59bd-97a3-0526b0fd90e2"

class ReaRBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="harbor-rear-unit-")
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.staging = root / "staging"
        self.system = root / "mnt-local"
        (self.staging / "volume-000" / "received").mkdir(parents=True)
        (self.staging / "boot-files" / "boot-000").mkdir(parents=True)
        (self.system / "boot").mkdir(parents=True)
        self.catalog = {
            "status": "completed_btrfs_and_boot_files",
            "bootable": False,
            "members": [{
                "status": "completed",
                "original_mount": "/",
                "snapshot_uuid": UUID,
            }],
            "boot_members": [{
                "status": "completed",
                "mount_point": "/boot",
                "filesystem": "vfat",
            }],
        }
    def _probe(self, path):
        return UUID if path.name == "received" else None
    def _filesystem(self, path):
        return "vfat" if path == self.system / "boot" else "btrfs"
    def _plan(self, catalog=None):
        return plan_rear_restore(
            catalog or self.catalog, self.staging, self.system,
            probe=self._probe, filesystem=self._filesystem,
        )
    def test_root_and_efi_plan_native_order(self):
        result = self._plan()
        self.assertEqual([x.original_mount for x in result], ["/", "/boot"])
        self.assertFalse(result[0].is_boot_files)
        self.assertTrue(result[1].is_boot_files)
        self.assertEqual(result[0].source.name, "received")
    def test_incomplete_backup_rejected(self):
        bad = copy.deepcopy(self.catalog)
        bad["status"] = "sending"
        with self.assertRaises(ValueError):
            self._plan(bad)
    def test_spoofed_bootable_catalog_rejected(self):
        bad = copy.deepcopy(self.catalog)
        bad["bootable"] = True
        with self.assertRaises(ValueError):
            self._plan(bad)
    def test_efi_mount_absent_rejected(self):
        (self.system / "boot").rmdir()
        with self.assertRaises(ValueError):
            self._plan()
    def test_boot_mount_fs_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            plan_rear_restore(
                self.catalog, self.staging, self.system,
                probe=self._probe, filesystem=lambda _: "btrfs",
            )
    def test_missing_received_uuid_rejected(self):
        with self.assertRaises(ValueError):
            plan_rear_restore(
                self.catalog, self.staging, self.system,
                probe=lambda _: None, filesystem=self._filesystem,
            )
    def test_symlink_into_external_target_rejected(self):
        (self.system / "boot").rmdir()
        (self.system / "boot").symlink_to(self.staging, target_is_directory=True)
        with self.assertRaises(ValueError):
            self._plan()
    def test_duplicate_root_mounts_rejected(self):
        bad = copy.deepcopy(self.catalog)
        bad["members"].append(copy.deepcopy(bad["members"][0]))
        (self.staging / "volume-001" / "received").mkdir(parents=True)
        with self.assertRaises(ValueError):
            self._plan(bad)
    def test_fstab_replaces_only_recorded_uuid(self):
        contents = (
            "# do not change UUID=a-old\n"
            "UUID=a-old / btrfs rw,subvol=@ 0 0\n"
            "PARTUUID=b-old /boot vfat defaults 0 2\n"
            "tmpfs /run tmpfs defaults 0 0\n"
        )
        output = reconcile_fstab(
            contents,
            {"/": ("a-old", None), "/boot": (None, "b-old")},
            {"/": ("a-new", None), "/boot": (None, "b-new")},
        )
        self.assertIn("UUID=a-new / btrfs rw,subvol=@ 0 0", output)
        self.assertIn("PARTUUID=b-new /boot vfat defaults 0 2", output)
        self.assertIn("# do not change UUID=a-old", output)
        self.assertIn("tmpfs /run tmpfs", output)
    def test_fstab_unknown_critical_mount_rejected(self):
        with self.assertRaises(ValueError):
            reconcile_fstab(
                "UUID=abc /secret ext4 defaults 0 2\n",
                {"/": ("abc", None)}, {"/": ("def", None)}
            )
    def test_fstab_old_uuid_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            reconcile_fstab(
                "UUID=unexpected / btrfs rw 0 0\n",
                {"/": ("expected", None)}, {"/": ("fresh", None)}
            )
    def test_recorded_uuid_preserves_distinct_boot_mounts(self):
        result = recorded_uuids({"blockdevices": [
            {"mountpoints":["/"],"uuid":UUID,"partuuid":"first"},
            {"mountpoints":["/boot"],"uuid":"a-efi","partuuid":"second"},
        ]})
        self.assertEqual(result["/"], (UUID, "first"))
        self.assertEqual(result["/boot"], ("a-efi", "second"))
    def test_ambiguous_disk_layout_rejected(self):
        with self.assertRaises(ValueError):
            recorded_uuids({"blockdevices": [
                {"mountpoints":["/"],"uuid":UUID},
                {"mountpoints":["/"],"uuid":ALT},
            ]})

if __name__ == "__main__":
    unittest.main()
