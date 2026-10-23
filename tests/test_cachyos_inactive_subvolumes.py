"""Inactive backup-root preparation: dry probes and mocked Btrfs ioctls."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from btrfs_backup_ng.core.cachyos_activation_plan import ActivationPlan
from btrfs_backup_ng.core.cachyos_inactive_subvolumes import (
    prepare_inactive_subvolumes,
)


class InactiveRootTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="harbor-inactive-")
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.staging = self.parent / "staging"
        self.top = self.parent / "top-level"
        self.staging.mkdir()
        self.top.mkdir()
        self.root = self.staging / "received-root"
        self.home = self.staging / "received-home"
        self.root.mkdir()
        self.home.mkdir()
        self.plan = ActivationPlan(
            set_id="55555555-5555-4555-8555-555555555555",
            source_hostname="Pegasus", target_hostname="Celestra",
            fresh_machine_id="0" * 32,
            mounts=(("/", "/@harbor-55555555-root"),
                    ("/home", "/@harbor-55555555-home")),
            fstab="", limine_cmdline="", bootloader="limine",
        )
        self.calls = []

    def run_btrfs(self, args, **kwargs):
        self.calls.append(args)
        if args[:3] == ["btrfs", "property", "get"]:
            return subprocess.CompletedProcess(args, 0, stdout="ro=true\n", stderr="")
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    def execute(self, **kwargs):
        defaults = dict(staging=self.staging, top_level=self.top,
                        probe_mount=lambda _: ("btrfs", "rw,subvolid=5"),
                        probe_uuid=lambda _: "beef-uuid",
                        run=self.run_btrfs)
        defaults.update(kwargs)
        with patch("btrfs_backup_ng.core.cachyos_inactive_subvolumes.os.geteuid",
                   return_value=0):
            return prepare_inactive_subvolumes(
                self.plan, {"/": self.root, "/home": self.home}, **defaults
            )

    def test_creates_only_namespaced_inactive_snapshots(self):
        result = self.execute()
        self.assertEqual(len(result), 2)
        writes = [call for call in self.calls
                  if call[:3] == ["btrfs", "subvolume", "snapshot"]]
        self.assertEqual(len(writes), 2)
        self.assertTrue(all(dest.startswith(str(self.top / "@harbor-55555555-"))
                            for *_, dest in writes))
        self.assertFalse(any("delete" in str(call) or "mount" in str(call)
                             or "limine" in str(call) for call in self.calls))

    def test_existing_target_fails_before_any_write(self):
        (self.top / "@harbor-55555555-home").mkdir()
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.execute()
        self.assertFalse(any(call[:3] == ["btrfs", "subvolume", "snapshot"]
                             for call in self.calls))

    def test_different_filesystem_uuid_refused(self):
        with self.assertRaisesRegex(ValueError, "do not belong"):
            self.execute(probe_uuid=lambda path: "old-fs" if path == self.staging
                         else "fresh-fs")
        self.assertEqual(self.calls, [])

    def test_not_top_level_btrfs_refused(self):
        with self.assertRaisesRegex(ValueError, "subvolid=5"):
            self.execute(probe_mount=lambda _: ("btrfs", "subvolid=256"))
        self.assertEqual(self.calls, [])

    def test_non_readonly_received_source_refused(self):
        def bad(args, **kwargs):
            self.calls.append(args)
            return subprocess.CompletedProcess(args, 0, stdout="ro=false\n", stderr="")
        with self.assertRaisesRegex(ValueError, "readonly"):
            self.execute(run=bad)
        self.assertFalse(any(c[:3] == ["btrfs", "subvolume", "snapshot"]
                             for c in self.calls))

    def test_unprivileged_refused(self):
        with patch("btrfs_backup_ng.core.cachyos_inactive_subvolumes.os.geteuid",
                   return_value=1000):
            with self.assertRaises(PermissionError):
                prepare_inactive_subvolumes(
                    self.plan, {"/": self.root, "/home": self.home},
                    staging=self.staging, top_level=self.top,
                )


if __name__ == "__main__":
    unittest.main()
