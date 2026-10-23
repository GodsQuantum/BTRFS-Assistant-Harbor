"""No host OS, EFI, bootloader or LUKS writes: mock disposable inactive root."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from btrfs_backup_ng.core.cachyos_activation_plan import ActivationPlan
from btrfs_backup_ng.core.cachyos_inactive_config import (
    planned_limine_config, configure_inactive_root,
)

S = "55555555-5555-4555-8555-555555555555"
M = "0" * 32
UUID = "33333333-3333-4333-8333-333333333333"
CMD = ("quiet rw rootflags=subvol=/@harbor-55555555-root "
       f"rd.luks.uuid={UUID} root=/dev/mapper/luks-{UUID}")
NATIVE = ('ESP_PATH="/boot"\n'
          f'KERNEL_CMDLINE[default]+="rw rootflags=subvol=/@ rd.luks.uuid={UUID}"\n'
          'BOOT_ORDER="*, *lts"\n')


class InactiveConfigTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="harbor-config-")
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.restored = self.parent / "@harbor-55555555-root"
        (self.restored / "etc/default").mkdir(parents=True)
        for name, contents in (
            ("etc/fstab", "UUID=OLD / btrfs defaults,subvol=/@ 0 0\n"),
            ("etc/hostname", "Pegasus\n"),
            ("etc/machine-id", "f" * 32 + "\n"),
            ("etc/default/limine", "OLD_LIMINE_OLD_UUID\n"),
        ):
            (self.restored / name).write_text(contents)
        self.plan = ActivationPlan(
            set_id=S, source_hostname="Pegasus", target_hostname="NewPegasus",
            fresh_machine_id=M,
            mounts=(("/", "/@harbor-55555555-root"),),
            fstab=("UUID=22222222-2222-4222-8222-222222222222 / btrfs "
                   "defaults,subvol=/@harbor-55555555-root 0 0\n"),
            limine_cmdline=CMD, bootloader="limine",
        )

    def run_prep(self, **kwargs):
        with patch("btrfs_backup_ng.core.cachyos_inactive_config.os.geteuid",
                   return_value=0):
            return configure_inactive_root(
                self.plan, self.restored,
                fresh_limine_config=NATIVE,
                fresh_crypttab="",
                **kwargs,
            )

    def test_materializes_new_root_only(self):
        output = self.run_prep()
        self.assertFalse(output["bootable_certified"])
        self.assertFalse(output["bootloader_invoked"])
        self.assertEqual((self.restored / "etc/hostname").read_text(),
                         "NewPegasus\n")
        self.assertEqual((self.restored / "etc/machine-id").read_text(),
                         M + "\n")
        self.assertEqual((self.restored / "etc/crypttab").read_text(), "")
        self.assertIn("@harbor-55555555-root",
                      (self.restored / "etc/fstab").read_text())
        limine = (self.restored / "etc/default/limine").read_text()
        self.assertIn("KERNEL_CMDLINE[default]=", limine)
        self.assertIn(CMD, limine)
        self.assertNotIn("OLD_LIMINE", limine)
        self.assertFalse((self.parent / "EFI").exists())
        self.assertFalse((self.parent / "limine.conf").exists())

    def test_symlink_existing_identity_fails_preflight_without_partial_changes(self):
        path = self.restored / "etc/machine-id"
        path.unlink()
        path.symlink_to("/etc/hosts")
        old = (self.restored / "etc/fstab").read_text()
        with self.assertRaisesRegex(ValueError, "invalid restored"):
            self.run_prep()
        self.assertEqual((self.restored / "etc/fstab").read_text(), old)

    def test_only_selected_backup_root_allowed(self):
        self.restored.rename(self.parent / "@")
        self.restored = self.parent / "@"
        with self.assertRaisesRegex(ValueError, "safe inactive"):
            self.run_prep()

    def test_limine_override_cannot_silently_use_old_disk(self):
        with self.assertRaisesRegex(ValueError, "overrides"):
            planned_limine_config(
                NATIVE+'KERNEL_CMDLINE[linux-cachyos]="root=/dev/mapper/old"\n',
                CMD)

    def test_actual_exact_mountpoint_is_rejected(self):
        with patch("btrfs_backup_ng.core.cachyos_inactive_config._exact_mountpoint",
                   return_value=True):
            with self.assertRaisesRegex(ValueError, "safe inactive"):
                self.run_prep()
        self.assertEqual((self.restored / "etc/hostname").read_text(), "Pegasus\\n".replace("\\n", "\n"))

    def test_synthetic_btrfs_subvol_device_is_not_treated_as_mount(self):
        # Linux Btrfs subvolumes can make Path.is_mount() return TRUE due
        # to synthetic st_dev, even when mountinfo lists no mount.
        with patch.object(Path, "is_mount", side_effect=AssertionError(
                "Path.is_mount() MUST NOT be used to guard Btrfs subvolume roots")):
            self.assertFalse(self.run_prep()["bootable_certified"])

    def test_untrusted_shell_interpolation_refused(self):
        with self.assertRaisesRegex(ValueError, "unsafe"):
            planned_limine_config(NATIVE, CMD+' $(rm -rf /)')

    def test_not_executable_by_unprivileged_user(self):
        with patch("btrfs_backup_ng.core.cachyos_inactive_config.os.geteuid",
                   return_value=1000):
            with self.assertRaises(PermissionError):
                configure_inactive_root(self.plan, self.restored,
                                        fresh_crypttab="", fresh_limine_config=NATIVE)


if __name__ == "__main__":
    unittest.main()
