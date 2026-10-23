"""Limine uses current native kernels; no EFI edit until verified QEMU boot."""
from dataclasses import replace
import unittest

from btrfs_backup_ng.core.cachyos_activation_plan import ActivationPlan
from btrfs_backup_ng.core.cachyos_limine_recovery_entry import preview_recovery_menu

SET="55555555-5555-4555-8555-555555555555"
OLD="44444444-4444-4444-8444-444444444444"
NEW="33333333-3333-4333-8333-333333333333"
CONFIG=(
    "timeout: 5\n"
    "default_entry: 2\n"
    "remember_last_entry: yes\n"
    "/+CachyOS\n"
    "  //linux-cachyos\n"
    "  comment: Kernel version: 7.3.0-3-cachyos\n"
    "  comment: kernel-id=linux-cachyos\n"
    "  protocol: linux\n"
    "  module_path: boot():/firmware/7.3.0/initramfs.img\n"
    "  path: boot():/firmware/7.3.0/vmlinuz\n"
    f"  cmdline: quiet rootflags=subvol=/@ rd.luks.uuid={OLD} "
    f"root=/dev/mapper/luks-{OLD}\n"
    "  //linux-cachyos-lts\n"
    "  comment: Kernel version: 6.18.55-2-cachyos-lts\n"
    "  protocol: linux\n"
    "  module_path: boot():/firmware/lts/initramfs.img\n"
    "  path: boot():/firmware/lts/vmlinuz\n"
    f"  cmdline: quiet rootflags=subvol=/@ rd.luks.uuid={OLD} "
    f"root=/dev/mapper/luks-{OLD}\n"
    "     ///1782 SNAPSHOT\n"
    "     ////linux-cachyos\n"
    "     protocol: linux\n"
    "     module_path: boot():/malicious/old-initramfs.img\n"
    "     path: boot():/malicious/old-vmlinuz\n"
    "     cmdline: rootflags=subvol=/@/.snapshots/1782/snapshot\n"
)
CMD=("quiet rw rootflags=subvol=/@harbor-55555555-root "
     f"rd.luks.uuid={NEW} root=/dev/mapper/luks-{NEW}")


class LimineBootMenuPreviewTest(unittest.TestCase):
    def setUp(self):
        self.plan=ActivationPlan(
            set_id=SET,source_hostname="Pegasus",target_hostname="NewPegasus",
            fresh_machine_id="0"*32,
            mounts=(("/", "/@harbor-55555555-root"),),
            fstab="",limine_cmdline=CMD,bootloader="limine",
        )

    def test_additive_entries_preserve_current_default_and_luks(self):
        result=preview_recovery_menu(
            CONFIG,self.plan,
            restored_module_versions={"7.3.0-3-cachyos","6.18.55-2-cachyos-lts"}
        )
        self.assertEqual(result.selected_kernel_ids,
                         ("linux-cachyos","linux-cachyos-lts"))
        self.assertEqual(result.menu_addition.count("cmdline:"),2)
        self.assertIn(CMD,result.menu_addition)
        self.assertNotIn(OLD,result.menu_addition)
        self.assertNotIn("malicious",result.menu_addition)
        self.assertIn("default_entry: 2",CONFIG)
        self.assertFalse(result.bootable_certified)
        self.assertTrue(result.existing_configuration_untouched)

    def test_missing_matching_modules_fails(self):
        with self.assertRaisesRegex(ValueError,"no native kernel"):
            preview_recovery_menu(
                CONFIG,self.plan,
                restored_module_versions={"5.1.0-unsupported"},
            )

    def test_native_snapshot_entry_is_not_selected(self):
        result=preview_recovery_menu(
            CONFIG,self.plan,
            restored_module_versions={"7.3.0-3-cachyos"},
        )
        self.assertEqual(result.menu_addition.count("cmdline:"),1)
        self.assertIn("/firmware/7.3.0",result.menu_addition)
        self.assertNotIn("/malicious",result.menu_addition)

    def test_untrusted_path_rejected(self):
        config=CONFIG.replace(
            "boot():/firmware/7.3.0/vmlinuz",
            "boot():/firmware/../etc/passwd",
        )
        with self.assertRaisesRegex(ValueError,"unsafe native Limine"):
            preview_recovery_menu(
                config,self.plan,
                restored_module_versions={"7.3.0-3-cachyos"},
            )

    def test_old_encrypted_root_is_never_reused(self):
        bad=replace(self.plan,limine_cmdline=CMD.replace(
            f"rd.luks.uuid={NEW}",f"rd.luks.uuid={NEW} rd.luks.uuid={OLD}"
        ))
        with self.assertRaisesRegex(ValueError,"untrusted target"):
            preview_recovery_menu(
                CONFIG,bad,
                restored_module_versions={"7.3.0-3-cachyos"},
            )

    def test_root_mapper_must_match_target_fresh_luks_uuid(self):
        bad=replace(self.plan,limine_cmdline=CMD.replace(
            f"root=/dev/mapper/luks-{NEW}",
            f"root=/dev/mapper/luks-{OLD}",
        ))
        with self.assertRaisesRegex(ValueError,"untrusted target"):
            preview_recovery_menu(
                CONFIG,bad,restored_module_versions={"7.3.0-3-cachyos"},
            )

    def test_duplicate_generation_refused(self):
        added=preview_recovery_menu(
            CONFIG,self.plan,
            restored_module_versions={"7.3.0-3-cachyos"}
        ).menu_addition
        with self.assertRaisesRegex(ValueError,"already present"):
            preview_recovery_menu(
                CONFIG+"\n"+added,self.plan,
                restored_module_versions={"7.3.0-3-cachyos"},
            )


if __name__ == "__main__":
    unittest.main()
