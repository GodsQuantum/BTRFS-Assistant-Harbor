"""ReaR single-root rescue guard regression tests; never touch any block device."""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

PROJECT = Path(__file__).resolve().parents[1]
HOOK = PROJECT / "backend/recovery/harbor-rear-restore"
CMAKE = PROJECT / "CMakeLists.txt"

class ReaRSafetyTests(unittest.TestCase):
    def test_bash_parser(self):
        subprocess.run(["bash", "-n", str(HOOK)], check=True)

    def test_missing_recovery_privilege_refuses_early(self):
        def drop_root():
            if os.geteuid() == 0:
                os.setgroups([])
                os.setgid(65534)
                os.setuid(65534)
        result = subprocess.run(
            ["bash", str(HOOK)],
            capture_output=True, text=True, check=False, timeout=10,
            preexec_fn=drop_root if os.geteuid() == 0 else None,
        )
        self.assertEqual(result.returncode, 71)
        self.assertIn("HARBOR_REAR_FAIL:NOT_ROOT", result.stderr)

    def test_profile_is_opt_in_and_requires_rear_rescue(self):
        text = HOOK.read_text()
        for marker in (
            "/etc/rear/rescue.conf",
            "/etc/btrfs-harbor/rear-rescue.conf",
            "single-root-uefi-grub-v1",
            "REAR_ROOT_NOT_BTRFS",
            "REAR_ESP_NOT_FAT32",
            "SECURE_BOOT_NOT_CERTIFIED",
            "INDEPENDENT_MOUNT_UNSUPPORTED",
            "NESTED_SUBVOLUMES_UNSUPPORTED",
            "CAS_VERIFICATION_FAILED",
            "ESP_HASH_MISMATCH",
            "STANDARD_GRUB_INSTALL_FAILED",
            "FALLBACK_GRUB_INSTALL_FAILED",
        ):
            self.assertIn(marker, text)
        self.assertNotIn("parted", text)
        self.assertNotIn("mkfs.", text)
        self.assertNotIn("HARBOR_REAR_QA_", text)

    def test_single_root_fstab_guard_rejects_other_mounted_data(self):
        source = HOOK.read_text()
        match = re.search(r'\n(awk \'.*?\' "\$src/etc/fstab") \|\| fail INDEPENDENT_MOUNT_UNSUPPORTED', source, re.S)
        self.assertIsNotNone(match)
        awk_command = match.group(1).split(" \"$src/etc/fstab\"")[0]
        with tempfile.TemporaryDirectory(prefix="harbor-rear-fstab-unit-") as t:
            path = Path(t) / "fstab"
            cases = {
                "UUID=x / btrfs defaults 0 0\nUUID=y /boot/efi vfat defaults 0 1\n": 0,
                "UUID=x / btrfs defaults 0 0\nUUID=y /boot/efi vfat defaults 0 1\nUUID=z /home btrfs subvol=@home 0 0\n": 1,
                "UUID=x / btrfs defaults 0 0\nUUID=y /boot/efi vfat defaults 0 1\nUUID=z /data ext4 defaults 0 2\n": 1,
                "UUID=x / btrfs defaults 0 0\n/dev/cdrom /media/cdrom iso9660 noauto 0 0\n": 0,
            }
            for data, should_fail in cases.items():
                path.write_text(data)
                # Only execute the AWK preflight extracted from the shipping hook.
                result = subprocess.run(
                    ["bash", "-c", awk_command + " \"$1\"", "bash", str(path)],
                    capture_output=True, text=True, timeout=8, check=False,
                )
                self.assertEqual(result.returncode != 0, bool(should_fail), data)

    def test_install_is_explicit_and_does_not_replace_system_rear_config(self):
        cmake = CMAKE.read_text()
        self.assertIn("backend/recovery/harbor-rear-restore", cmake)
        self.assertIn("backend/recovery/local.example.conf", cmake)
        self.assertIn("rear-recovery-profile-safety", cmake)
        self.assertNotIn("DESTINATION /etc/rear", cmake)
        sample = (PROJECT / "backend/recovery/local.example.conf").read_text()
        self.assertIn("BACKUP=EXTERNAL", sample)
        self.assertIn("EXTERNAL_RESTORE=", sample)
        self.assertIn("COPY_AS_IS+=", sample)
        self.assertIn("od tr awk", sample)
        self.assertNotIn("OUTPUT_URL=null", sample)

if __name__ == "__main__":
    unittest.main()
