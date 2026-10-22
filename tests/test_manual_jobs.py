"""No NAS, systemd, or physical workstation touched by these unit tests."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from backend import manual_jobs as job
from backend import cas_schedule as cas

GOOD = dict(config="root", repo="/mnt/NFS/Workstations", machine="Pegasus",
            number=21, owner_uid=1000)
SEND = ["harbor-transport", "send", "--repo", "/mnt/NFS/Workstations",
        "--name", "snap-root-21-20261022-uuid", "--machine", "Pegasus",
        "--snapshot", "/test/readonly/21", "--experimental", "--retries", "8"]


class DurableJobTests(unittest.TestCase):
    def fixture(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        root = base / "jobs"
        root.mkdir()
        return root

    def test_rejects_invalid_id_and_source(self):
        for bad in ("../a", "c", "a" * 36, "abc\n"):
            with self.assertRaises(ValueError):
                job.check_id(bad)
        with self.assertRaises(ValueError):
            job.recorded_archive({"command": SEND[:SEND.index("--machine")] +
                                  ["--machine", "Malicious;touch"] + SEND[SEND.index("--machine")+2:]})

    def test_atomic_registry_no_real_service(self):
        root = self.fixture()
        with patch.object(job, "check_store"), patch.object(job, "require_network_repo"), \
             patch.object(job, "snapshot_uuid", return_value="1234"):
            x = job.register(**GOOD, root=root, activate=False,
                             command_builder=lambda profile, selected_number: list(SEND))
            self.assertIn("id", x)
            self.assertEqual(job.load(x["id"], root)["state"], "queued")
            self.assertEqual((root / (x["id"]+".json")).stat().st_mode & 0o777, 0o600)
            with self.assertRaises(RuntimeError):
                job.register(**GOOD, root=root, activate=False,
                             command_builder=lambda profile, selected_number: list(SEND))
            self.assertEqual(len(job.all_jobs(root)), 1)

    def test_independent_job_persists_after_ui_disappears(self):
        root = self.fixture()
        with patch.object(job, "check_store"), patch.object(job, "require_network_repo"), \
             patch.object(job, "snapshot_uuid", return_value="1234"):
            first = job.register(**GOOD, root=root, activate=False,
                                 command_builder=lambda profile, selected_number: list(SEND))
        # New process is able to read the durable manifest; no QProcess is referenced.
        data = json.loads((root / (first["id"]+".json")).read_text())
        self.assertEqual(data["command"], SEND)
        self.assertEqual(data["state"], "queued")

    def test_manual_cancel_disables_only_job_without_deleting_archive(self):
        root = self.fixture()
        with patch.object(job, "check_store"), patch.object(job, "require_network_repo"), \
             patch.object(job, "snapshot_uuid", return_value="1234"):
            first = job.register(**GOOD, root=root, activate=False,
                                 command_builder=lambda profile, selected_number: list(SEND))
        cancelled = job.cancel(first["id"], root=root, perform_systemd=False)
        self.assertEqual(cancelled["state"], "cancelled")
        self.assertEqual(job.load(first["id"], root)["state"], "cancelled")
        self.assertTrue((root / (first["id"]+".json")).is_file())

    def test_replay_reuses_archive_name(self):
        root = self.fixture()
        with patch.object(job, "check_store"), patch.object(job, "require_network_repo"), \
             patch.object(job, "snapshot_uuid", return_value="1234"):
            first = job.register(**GOOD, root=root, activate=False,
                                 command_builder=lambda profile, selected_number: list(SEND))
        old = job.load(first["id"], root)["command"]
        new = job.load(first["id"], root)["command"]
        self.assertEqual(old, new)
        self.assertEqual(job.recorded_archive(job.load(first["id"], root)),
                         "m@Pegasus@snap-root-21-20261022-uuid")

    def test_verify_uses_original_uid_under_root_squash(self):
        root = self.fixture()
        with patch.object(job, "check_store"), patch.object(job, "require_network_repo"), \
             patch.object(job, "snapshot_uuid", return_value="1234"):
            job_doc = job.register(**GOOD, root=root, activate=False,
                                   command_builder=lambda profile, selected_number: list(SEND))
        doc = job.load(job_doc["id"], root)
        response = type("Result", (), {"stdout": "[]"})()
        with patch.object(job.subprocess, "run", return_value=response) as run:
            self.assertFalse(job.verify_committed(doc))
            self.assertEqual(run.call_args.kwargs["env"]["PKEXEC_UID"], "1000")

    def test_existing_verified_archive_skips_replaying_transfer(self):
        root = self.fixture()
        with patch.object(job, "check_store"), patch.object(job, "require_network_repo"), \
             patch.object(job, "snapshot_uuid", return_value="1234"):
            first = job.register(**GOOD, root=root, activate=False,
                                 command_builder=lambda profile, selected_number: list(SEND))
        with patch.object(job, "require_network_repo"), patch.object(job, "verify_committed", return_value=True), \
             patch.object(job, "disable_completed") as disabled, \
             patch.object(job.subprocess, "Popen") as backend:
            self.assertEqual(job.runner(first["id"], root=root), 0)
            backend.assert_not_called()
            disabled.assert_called_once_with(first["id"])
            self.assertEqual(job.load(first["id"], root)["state"], "completed")

    def test_old_scheduled_profiles_are_not_activated_by_manual_package(self):
        unit = Path(__file__).resolve().parents[1] / "packaging/systemd/btrfs-assistant-harbor-job@.service"
        content = unit.read_text()
        self.assertIn("Restart=on-failure", content)
        self.assertIn("WantedBy=multi-user.target", content)
        self.assertIn("KillMode=control-group", content)
        self.assertIn("run --id %i", content)
        self.assertNotIn("OnCalendar=", content)


class SelectedSnapshotTests(unittest.TestCase):
    def test_selected_snapshot_must_be_readonly_and_present(self):
        profile = type("P", (), dict(config="root", target="/tmp/repo",
                                      machine="Pegasus", allow_local=False))()
        snaps = {"root": [
            {"number": 10, "subvolume": "/"},
            {"number": 11, "subvolume": "/"},
            {"number": 12, "subvolume": "/"},
        ]}
        fake = type("Result", (), {"stdout": json.dumps(snaps)})()
        import unittest.mock as mock
        empty_inventory = type("Result", (), {"stdout": "[]"})()
        with patch.object(cas.subprocess, "run", side_effect=[fake, empty_inventory, fake, empty_inventory]), \
             patch.object(cas, "is_readonly_snapshot", return_value=True), \
             patch.object(cas, "snapshot_uuid", return_value="11111111-1111-4111-8111-111111111111"), \
             patch.object(cas, "build_machine_send") as builder:
            builder.return_value = ["harbor-transport", "send"]
            cas.build_send(profile, selected_number=11)
            available = builder.call_args.args[1]
            self.assertEqual([number for number, _ in available], [11, 10])
            with self.assertRaises(RuntimeError):
                cas.build_send(profile, selected_number=13)
            with self.assertRaises(ValueError):
                cas.build_send(profile, selected_number=-1)


if __name__ == "__main__":
    unittest.main()
