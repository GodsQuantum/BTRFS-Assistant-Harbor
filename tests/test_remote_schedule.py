import json
import tempfile
import unittest
import uuid
from pathlib import Path

from backend import remote_schedule as sched


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.profile = sched.Profile("root", "/mnt/Cloud Backup", "daily", False)

    def test_id_stable_and_valid(self):
        self.assertEqual(self.profile.profile_id, sched.Profile("root", "/mnt/Cloud Backup", "daily", False).profile_id)
        uuid.UUID(self.profile.profile_id)
        self.assertNotEqual(self.profile.profile_id, sched.Profile("home", "/mnt/Cloud Backup", "daily", False).profile_id)

    def test_frequencies(self):
        for frequency in ("hourly", "daily", "weekly"):
            timer = sched.timer_unit(self.profile, frequency)
            self.assertIn("Persistent=true", timer)
            self.assertIn(f"OnCalendar={frequency}", timer)
        with self.assertRaises(ValueError):
            sched.timer_unit(self.profile, "every 5 seconds")

    def test_validation_rejects_unsafe_inputs(self):
        for target in ("/", "", "relative", "/tmp/../etc", "/tmp/a\nExecStart=/bin/sh"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                sched.Profile("root", target, "daily", False)
        with self.assertRaises(ValueError):
            sched.Profile("root;id", "/mnt/backups", "daily", False)

    def test_units_have_safe_exec_and_retry(self):
        unit = sched.service_unit(self.profile, "/usr/libexec/btrfs-assistant-harbor/remote_schedule.py")
        self.assertIn("Restart=on-failure", unit)
        self.assertIn("RestartSec=60s", unit)
        self.assertIn("NoNewPrivileges=true", unit)
        self.assertNotIn("sh -c", unit)
        self.assertIn(self.profile.profile_id, unit)
        with self.assertRaises(ValueError):
            sched.service_unit(self.profile, "/tmp/unsafe script.sh")

    def test_cli_argv_is_constant_and_has_no_shell(self):
        args = sched.schedule_argv(self.profile, "/usr/bin/btrfs-backup-ng")
        self.assertEqual(args[0], "/usr/bin/btrfs-backup-ng")
        self.assertEqual(args[1:4], ["raw", "checkpoint-v2", "schedule-run"])
        self.assertIn("--experimental", args)
        self.assertNotIn("--allow-local", args)
        self.assertEqual(args[args.index("--target") + 1], "/mnt/Cloud Backup")

    def test_profile_serialization_round_trip(self):
        data = json.loads(json.dumps(self.profile.as_dict()))
        self.assertEqual(sched.Profile.from_dict(data), self.profile)
        data["profile_id"] = "ffffffff-ffff-4fff-8fff-ffffffffffff"
        with self.assertRaises(ValueError):
            sched.Profile.from_dict(data)

    def test_cas_profile_has_distinct_identity_and_uid(self):
        cas = sched.Profile("root", "/mnt/Cloud Backup", "daily", False, "cas", 1000)
        self.assertNotEqual(self.profile.profile_id, cas.profile_id)
        self.assertEqual(cas.as_dict()["version"], 2)
        self.assertEqual(sched.Profile.from_dict(cas.as_dict()), cas)
        self.assertIn("OnCalendar=daily", sched.timer_unit(cas, "daily"))
        self.assertIn("Restart=on-failure", sched.service_unit(cas, "/usr/bin/btrfs-assistant-harbor-schedule"))
        with self.assertRaises(ValueError):
            sched.Profile("root", "/mnt/Cloud Backup", "daily", False, "cas", 0)
        with self.assertRaises(ValueError):
            sched.Profile("root", "/mnt/Cloud Backup", "daily", False, "cas", None)
        tampered = cas.as_dict()
        tampered["owner_uid"] = 0
        with self.assertRaises(ValueError):
            sched.Profile.from_dict(tampered)

    def test_disable_schedule_only_deletes_its_owned_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profiles = root / "profiles"
            units = root / "units"
            first = sched.Profile("root", "/mnt/NFS", "daily")
            second = sched.Profile("home", "/mnt/NFS", "weekly")
            owned = sched.install_profile(first, profiles, units, "/usr/bin/btrfs-assistant-harbor-schedule")
            retained = sched.install_profile(second, profiles, units, "/usr/bin/btrfs-assistant-harbor-schedule")
            removed = sched.remove_profile(first.profile_id, profiles, units, activate=False)
            self.assertEqual(owned, removed)
            self.assertTrue(all(not p.exists() for p in removed))
            self.assertTrue(all(p.exists() for p in retained))
            self.assertEqual(len(sched.list_profiles(profiles)), 1)
            with self.assertRaises((ValueError, FileNotFoundError)):
                sched.remove_profile(first.profile_id, profiles, units, activate=False)

    def test_staging_files_written_only_in_explicit_temp_roots(self):
        with tempfile.TemporaryDirectory() as tmp:
            etc = Path(tmp) / "etc"
            units = Path(tmp) / "units"
            installed = sched.install_profile(self.profile, etc, units, "/usr/libexec/btrfs-assistant-harbor/remote_schedule.py")
            self.assertEqual(len(installed), 3)
            self.assertTrue(all(p.is_file() for p in installed))
            self.assertEqual((etc / (self.profile.profile_id + ".json")).stat().st_mode & 0o777, 0o600)
            self.assertFalse((units / ("btrfs-assistant-harbor-" + self.profile.profile_id + ".timer")).is_symlink())


if __name__ == "__main__":
    unittest.main()
