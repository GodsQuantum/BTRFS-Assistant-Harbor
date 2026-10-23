"""Pure boot activation planning. Absolutely no source/disk/ESP writes."""
import copy
import unittest

from btrfs_backup_ng.core.cachyos_activation_plan import plan_cachyos_activation

OLD_FS = "11111111-1111-4111-8111-111111111111"
NEW_FS = "22222222-2222-4222-8222-222222222222"
NEW_LUKS = "33333333-3333-4333-8333-333333333333"
OLD_LUKS = "44444444-4444-4444-8444-444444444444"
SET = "55555555-5555-4555-8555-555555555555"

OLD_FSTAB = (
    f"UUID={OLD_FS} / btrfs defaults,subvol=/@ 0 0\n"
    f"UUID={OLD_FS} /home btrfs defaults,subvol=/@home 0 0\n"
    "UUID=eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee /boot vfat defaults 0 2\n"
)
NEW_FSTAB = (
    f"UUID={NEW_FS} / btrfs rw,relatime,compress=zstd:3,subvol=/@ 0 0\n"
    f"UUID={NEW_FS} /home btrfs rw,relatime,subvol=/@home 0 0\n"
    "UUID=aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa /boot vfat defaults 0 2\n"
)
FRESH_CMDLINE = (
    f"quiet splash rw rootflags=subvol=/@ rd.luks.uuid={NEW_LUKS} "
    f"root=/dev/mapper/luks-{NEW_LUKS} zswap.enabled=1"
)
OS = "ID=cachyos\nPRETTY_NAME=CachyOS\n"


class FreshInstallActivationPlanTest(unittest.TestCase):
    def setUp(self):
        self.catalog = {
            "set_id": SET,
            "machine_name": "Pegasus",
            "status": "completed_btrfs_and_boot_files",
            "bootable": False,
            "members": [
                {"original_mount": "/", "status": "completed"},
                {"original_mount": "/home", "status": "completed"},
            ],
            "boot_members": [
                {"mount_point": "/boot", "filesystem": "vfat", "status": "completed"}
            ],
        }
        self.args = {
            "source_os_release": OS,
            "fresh_os_release": OS,
            "source_fstab": OLD_FSTAB,
            "fresh_fstab": NEW_FSTAB,
            "fresh_limine_cmdline": FRESH_CMDLINE,
            "fresh_machine_id": "0" * 32,
            "current_hostname": "NewPegasus",
            "hostname_policy": "original",
        }

    def plan(self):
        return plan_cachyos_activation(self.catalog, **self.args)

    def test_original_name_preserve_fresh_luks_and_fresh_machine_id(self):
        result = self.plan()
        self.assertEqual(result.target_hostname, "Pegasus")
        self.assertEqual(result.fresh_machine_id, "0" * 32)
        self.assertIn(f"rd.luks.uuid={NEW_LUKS}", result.limine_cmdline)
        self.assertIn(f"root=/dev/mapper/luks-{NEW_LUKS}", result.limine_cmdline)
        self.assertNotIn(OLD_LUKS, result.limine_cmdline)
        self.assertIn("rootflags=subvol=/@harbor-55555555-root", result.limine_cmdline)
        self.assertIn(f"UUID={NEW_FS}", result.fstab)
        self.assertNotIn(OLD_FS, result.fstab)
        self.assertIn("subvol=/@harbor-55555555-home", result.fstab)
        self.assertFalse(result.bootable_certified)
        self.assertTrue(result.requires_offline_activation)

    def test_keeps_fresh_or_explicit_new_host(self):
        self.args["hostname_policy"] = "installed"
        self.assertEqual(self.plan().target_hostname, "NewPegasus")
        self.args["hostname_policy"] = "custom"
        self.args["custom_hostname"] = "Celestra"
        self.assertEqual(self.plan().target_hostname, "Celestra")

    def test_missing_efi_never_gets_certified(self):
        self.catalog["boot_members"] = []
        with self.assertRaisesRegex(ValueError, "EFI"):
            self.plan()

    def test_incomplete_machine_set_never_gets_certified(self):
        self.catalog["status"] = "pending"
        with self.assertRaisesRegex(ValueError, "entire computer"):
            self.plan()

    def test_clone_never_carries_old_disk_uuid(self):
        self.args["fresh_limine_cmdline"] = FRESH_CMDLINE.replace(
            f"root=/dev/mapper/luks-{NEW_LUKS}",
            f"root=/dev/mapper/luks-{OLD_LUKS}",
        )
        with self.assertRaisesRegex(ValueError, "do not match"):
            self.plan()

    def test_unprotected_extra_data_partition_fails_closed(self):
        self.args["fresh_fstab"] += "UUID=bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb /data ext4 defaults 0 2\n"
        with self.assertRaisesRegex(ValueError, "unprotected new installation"):
            self.plan()

    def test_invalid_custom_hostname_fails_closed(self):
        self.args["hostname_policy"] = "custom"
        self.args["custom_hostname"] = "../../evil"
        with self.assertRaisesRegex(ValueError, "hostname invalid"):
            self.plan()

    def test_new_target_subvolumes_added_if_not_in_fresh_install(self):
        self.catalog["members"].append({"original_mount": "/srv", "status": "completed"})
        self.args["source_fstab"] += f"UUID={OLD_FS} /srv btrfs defaults,subvol=/@srv 0 0\n"
        result = self.plan()
        self.assertIn(f"UUID={NEW_FS} /srv btrfs defaults,subvol=/@harbor-55555555-srv 0 0",
                      result.fstab)

    def test_non_cachyos_source_refused(self):
        self.args["source_os_release"] = "ID=fedora\n"
        with self.assertRaisesRegex(ValueError, "CachyOS"):
            self.plan()

    def test_unsafe_or_duplicate_backup_mount_refused(self):
        self.catalog["members"].append({"original_mount": "/home", "status": "completed"})
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.plan()


if __name__ == "__main__":
    unittest.main()
