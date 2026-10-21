import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from backend.remote_schedule import Profile
from backend import cas_schedule


class MachineSchedules(unittest.TestCase):
    def test_profile_is_scoped_without_breaking_old_cas_profiles(self):
        base = Profile("root", "/mnt/Workstations", "daily",
                       engine="cas", owner_uid=1000)
        pegasus = Profile("root", "/mnt/Workstations", "daily",
                          engine="cas", owner_uid=1000, machine="Pegasus")
        galactica = Profile("root", "/mnt/Workstations", "daily",
                            engine="cas", owner_uid=1000, machine="Galactica")
        self.assertEqual(base.as_dict()["version"], 2)
        self.assertEqual(pegasus.as_dict()["version"], 3)
        self.assertNotEqual(pegasus.profile_id, galactica.profile_id)
        self.assertNotEqual(pegasus.profile_id, base.profile_id)
        self.assertEqual(Profile.from_dict(pegasus.as_dict()), pegasus)
        self.assertEqual(Profile.from_dict(base.as_dict()), base)
        with self.assertRaises(ValueError):
            Profile("root", "/mnt/Workstations", "daily",
                    engine="cas", owner_uid=1000, machine="../Galactica")

    def test_machine_send_uses_only_its_own_uuid_verified_parent(self):
        profile = Profile("root", "/mnt/Workstations", "daily",
                          engine="cas", owner_uid=1000, machine="Pegasus")
        root = "/.snapshots/"
        snapshots = [(12, Path(root+"12/snapshot")),
                     (11, Path(root+"11/snapshot"))]
        previous = "m@Pegasus@snap-root-11-20261020T120000Z-a5d970db"
        foreign = "m@Galactica@snap-root-11-20261020T120000Z-a5d970db"
        archives = [
            {"name": previous, "source_uuid": "12e7b692-9c63-43ce-bdb2-8295d8a4b34b"},
            {"name": foreign, "source_uuid": "12e7b692-9c63-43ce-bdb2-8295d8a4b34b"},
        ]
        def fake_uuid(path):
            return ("12e7b692-9c63-43ce-bdb2-8295d8a4b34b"
                    if "/11/" in str(path) else
                    "ac451d79-5b95-4375-8970-cddde7b83938")
        with patch.object(cas_schedule, "snapshot_uuid", side_effect=fake_uuid), \
             patch.object(cas_schedule.subprocess, "run",
                          return_value=SimpleNamespace(returncode=0)) as verify:
            cmd = cas_schedule.build_machine_send(profile, snapshots, archives, "harbor-transport")
        self.assertEqual(cmd[cmd.index("--machine") + 1], "Pegasus")
        self.assertEqual(cmd[cmd.index("--parent-archive") + 1], previous)
        self.assertIn("--parent", cmd)
        self.assertTrue(cmd[cmd.index("--name")+1].startswith("snap-root-12-"))
        self.assertEqual(verify.call_args.args[0][-1], previous)
        self.assertNotIn(foreign, cmd)

    def test_verified_backup_is_skipped_and_different_source_not_skipped(self):
        profile = Profile("root", "/mnt/Workstations", "daily",
                          engine="cas", owner_uid=1000, machine="Galactica")
        old = "m@Galactica@snap-root-12-20261020T120000Z-a5d970db"
        snap = [(12, Path("/.snapshots/12/snapshot"))]
        archives = [{"name": old, "source_uuid": "eb223a2f-00e2-40c2-b79a-b00d888f7b5a"}]
        with patch.object(cas_schedule, "snapshot_uuid",
                          return_value=archives[0]["source_uuid"]), \
             patch.object(cas_schedule.subprocess, "run",
                          return_value=SimpleNamespace(returncode=0)) as verify:
            self.assertIsNone(cas_schedule.build_machine_send(profile, snap, archives, "harbor-transport"))
            self.assertEqual(verify.call_args.args[0][-1], old)
        with patch.object(cas_schedule, "snapshot_uuid",
                          return_value="ac451d79-5b95-4375-8970-cddde7b83938"):
            self.assertIn("--machine", cas_schedule.build_machine_send(profile, snap, archives, "harbor-transport"))


if __name__ == "__main__":
    unittest.main()
