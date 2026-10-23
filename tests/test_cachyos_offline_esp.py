"""Offline VFAT boot-menu stage: additive, rollback copy, guarded by asset integrity."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from btrfs_backup_ng.core.cachyos_offline_esp import stage_additive_limine_entry
from btrfs_backup_ng.core.cachyos_limine_recovery_entry import preview_recovery_menu
from tests.test_cachyos_limine_recovery_entry import CONFIG, SET, CMD
from btrfs_backup_ng.core.cachyos_activation_plan import ActivationPlan


class OfflineEspTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="harbor-offline-esp-")
        self.addCleanup(self.tmp.cleanup)
        self.esp = Path(self.tmp.name)/"isolated-esp"
        self.esp.mkdir()
        self.original = CONFIG
        (self.esp/"limine.conf").write_text(CONFIG)
        for name in ("vmlinuz", "initramfs.img"):
            file = self.esp / "firmware/7.3.0" / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(("dummy-image-" + name).encode())
        self.plan = ActivationPlan(
            set_id=SET, source_hostname="Pegasus", target_hostname="NewPegasus",
            fresh_machine_id="0"*32,
            mounts=(("/", "/@harbor-"+SET[:8]+"-root"),),
            fstab="", limine_cmdline=CMD, bootloader="limine",
        )
        self.preview = preview_recovery_menu(
            CONFIG,self.plan,restored_module_versions={"7.3.0-3-cachyos"},
            secure_boot_state="disabled")

    def stage(self, **kwargs):
        settings = dict(
            set_id=SET, secure_boot_state="disabled",
            probe_esp=lambda _: True,
        )
        settings.update(kwargs)
        with patch("btrfs_backup_ng.core.cachyos_offline_esp.os.geteuid",
                   return_value=0):
            return stage_additive_limine_entry(self.esp,self.preview,**settings)

    def test_preserves_original_and_only_adds_recovery_alternative(self):
        result = self.stage()
        self.assertTrue(result["default_selection_preserved"])
        self.assertFalse(result["bootable_certified"])
        self.assertFalse(result["reboot_performed"])
        self.assertEqual(Path(result["backup_file"]).read_text(),self.original)
        current = (self.esp/"limine.conf").read_text()
        self.assertTrue(current.startswith(self.original))
        self.assertTrue(current.endswith(self.preview.menu_addition))
        self.assertIn("default_entry: 2",current)

    def test_missing_boot_image_refused_before_any_change(self):
        (self.esp/"firmware/7.3.0/initramfs.img").unlink()
        with self.assertRaisesRegex(ValueError,"missing or unsafe"):
            self.stage()
        self.assertEqual((self.esp/"limine.conf").read_text(),self.original)

    def test_tampered_hash_of_kernel_refused_before_any_change(self):
        asset = self.esp/"firmware/7.3.0/vmlinuz"
        actual = hashlib.blake2b(asset.read_bytes()).hexdigest()
        self.preview = preview_recovery_menu(
            CONFIG.replace(
                "path: boot():/firmware/7.3.0/vmlinuz",
                "path: boot():/firmware/7.3.0/vmlinuz#"+actual,
            ),self.plan,restored_module_versions={"7.3.0-3-cachyos"},
            secure_boot_state="disabled",
        )
        asset.write_bytes(b"tampered-image")
        with self.assertRaisesRegex(ValueError,"checksum mismatch"):
            self.stage()
        self.assertEqual((self.esp/"limine.conf").read_text(),self.original)

    def test_verified_hash_succeeds(self):
        asset = self.esp/"firmware/7.3.0/vmlinuz"
        actual = hashlib.blake2b(asset.read_bytes()).hexdigest()
        self.preview = preview_recovery_menu(
            CONFIG.replace(
                "path: boot():/firmware/7.3.0/vmlinuz",
                "path: boot():/firmware/7.3.0/vmlinuz#"+actual,
            ),self.plan,restored_module_versions={"7.3.0-3-cachyos"},
            secure_boot_state="disabled",
        )
        self.assertFalse(self.stage()["bootable_certified"])

    def test_secure_boot_refused(self):
        with self.assertRaisesRegex(ValueError,"Secure Boot"):
            self.stage(secure_boot_state="unknown")
        with self.assertRaisesRegex(ValueError,"Secure Boot"):
            self.stage(secure_boot_state="enabled")

    def test_fake_vfat_mount_refused(self):
        with self.assertRaisesRegex(ValueError,"mounted isolated FAT32"):
            self.stage(probe_esp=lambda _: False)

    def test_repeated_staging_refused_with_backup_retained(self):
        result=self.stage()
        with self.assertRaisesRegex(ValueError,"appendable baseline"):
            self.stage()
        self.assertEqual(Path(result["backup_file"]).read_text(),self.original)

    def test_symlink_original_refused(self):
        (self.esp/"limine.conf").unlink()
        (self.esp/"limine.conf").symlink_to("/etc/hosts")
        with self.assertRaises(OSError):
            self.stage()


if __name__ == "__main__":
    unittest.main()
