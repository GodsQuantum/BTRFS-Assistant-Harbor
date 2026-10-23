"""Read-only recovery preflight on synthetic fake OS roots; no disks involved."""
from __future__ import annotations
from contextlib import ExitStack
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from btrfs_backup_ng.core import cachyos_activation_probe as probe
from tests.test_cachyos_activation_plan import (
    SET, NEW_LUKS, NEW_FSTAB, OLD_FSTAB, OS, FRESH_CMDLINE,
)


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="harbor-readonly-recovery-")
        self.addCleanup(self.tmp.cleanup)
        self.staging = Path(self.tmp.name) / "staging"
        self.staging.mkdir()
        self.source = Path(self.tmp.name) / "received"
        (self.source / "etc").mkdir(parents=True)
        (self.source / "etc/os-release").write_text(OS)
        (self.source / "etc/fstab").write_text(OLD_FSTAB)
        self.catalog = {
            "set_id": SET, "machine_name": "Pegasus",
            "status": "completed_btrfs_and_boot_files",
            "bootable": False,
            "members": [
                {"original_mount": "/", "status": "completed",
                 "snapshot_uuid": "66666666-6666-4666-8666-666666666666"},
                {"original_mount": "/home", "status": "completed"},
            ],
            "boot_members": [
                {"mount_point": "/boot", "filesystem": "vfat", "status": "completed"}
            ],
        }
        self.intent = {
            "version": 1, "set_id": SET, "source_machine": "Pegasus",
            "hostname_policy": "original", "target_hostname": "Pegasus",
            "boot_activation_certified": False,
        }
        self.intent_path = self.staging / ".harbor-recovery-intent.json"
        self.write_intent()
        self.read_text = Path.read_text
        self.is_file = Path.is_file

    def write_intent(self):
        self.intent_path.write_text(json.dumps(self.intent))
        self.intent_path.chmod(0o600)

    def patched(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(mock.patch.object(probe.os, "geteuid", return_value=0))
        stack.enter_context(mock.patch.object(probe, "_mount_filesystem",
                       side_effect=lambda x: "vfat" if x == "/boot" else "btrfs"))
        stack.enter_context(mock.patch.object(probe, "find_received_subvolume",
                                             return_value=self.source))
        stack.enter_context(mock.patch.object(probe.shutil, "which",
                                             return_value="/usr/bin/limine-mkinitcpio"))
        stack.enter_context(mock.patch.object(probe.socket, "gethostname",
                                             return_value="NewPegasus"))
        stack.enter_context(mock.patch.object(probe, "_active_root_mapper",
                           return_value="/dev/mapper/luks-" + NEW_LUKS))
        stack.enter_context(mock.patch.object(Path, "is_file",
            autospec=True, side_effect=lambda p: (
                True if str(p) in ("/boot/limine.conf", "/etc/default/limine")
                else self.is_file(p))))
        mapping = {
            "/proc/cmdline": FRESH_CMDLINE,
            "/etc/fstab": NEW_FSTAB,
            "/etc/os-release": OS,
            "/etc/machine-id": "0" * 32 + "\n",
        }
        stack.enter_context(mock.patch.object(Path, "read_text", autospec=True,
            side_effect=lambda p, **kw: mapping[str(p)] if str(p) in mapping
            else self.read_text(p, **kw)))
        return stack

    def test_preflight_preserves_fresh_keys_and_stays_readonly(self):
        with self.patched():
            out = probe.probe_installed_cachyos(self.catalog, self.staging)
        self.assertEqual(out["source_machine"], "Pegasus")
        self.assertEqual(out["target_hostname"], "Pegasus")
        self.assertTrue(out["preserve_fresh_luks_uuid_and_passphrase"])
        self.assertEqual(out["volumes"], 2)
        self.assertFalse(out["bootable_certified"])
        self.assertFalse(out["activation_performed"])
        self.assertEqual(list(self.staging.iterdir()), [self.intent_path])

    def test_intent_for_other_machine_is_rejected(self):
        self.intent["source_machine"] = "Celestra"
        self.write_intent()
        with self.patched():
            with self.assertRaisesRegex(ValueError, "wrong source machine"):
                probe.probe_installed_cachyos(self.catalog, self.staging)

    def test_symlink_escape_of_source_fstab_is_rejected(self):
        escaped = self.source / "etc/fstab"
        escaped.unlink()
        escaped.symlink_to("/etc/hosts")
        with self.patched():
            with self.assertRaisesRegex(ValueError, "escapes"):
                probe.probe_installed_cachyos(self.catalog, self.staging)

    def test_fresh_root_unencrypted_or_mapper_wrong_is_rejected(self):
        with self.patched(), mock.patch.object(
            probe, "_active_root_mapper", return_value="/dev/mapper/wrong"
        ):
            with self.assertRaisesRegex(ValueError, "LUKS mapper"):
                probe.probe_installed_cachyos(self.catalog, self.staging)


if __name__ == "__main__":
    unittest.main()
