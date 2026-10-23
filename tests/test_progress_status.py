"""Isolated estimate and security tests, no actual Btrfs sends."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from backend import progress_status as p


class ProgressTests(unittest.TestCase):
    def sample(self):
        return dict(id="e9ae1ccd-36e6-4cdd-81e5-9341eefbe020",
                    state="running", attempts=1, created=10, last_started=10,
                    bytes_read=20 * p.GIB, owner_uid=1000, machine="Pegasus",
                    command=["harbor-transport", "send", "--snapshot", "/.snapshots/1/snapshot"],
                    repository="/mnt/Cloud9/backup-local/Workstations")

    def test_remaining_estimate_and_eta_are_explicit(self):
        j = self.sample()
        result = p.synthesize(j, 1010, None, 65 * p.GIB, True)
        self.assertAlmostEqual(result["stream_total_estimate"] / p.GIB, 72.8, delta=0.2)
        self.assertGreater(result["stream_remaining_estimate"], 50 * p.GIB)
        self.assertGreater(result["eta_seconds"], 1000)
        self.assertIsNone(result["uploaded_bytes"])
        self.assertTrue(result["estimate_is_approximate"])

    def test_new_upload_counter_and_network_prediction(self):
        j = self.sample()
        j.update(uploaded_bytes=3 * p.GIB, reused_bytes=7 * p.GIB,
                 upload_metrics_available=True)
        result = p.synthesize(j, 1010, None, 65 * p.GIB, True)
        self.assertEqual(result["uploaded_bytes"], 3 * p.GIB)
        self.assertGreater(result["network_remaining_estimate"], 0)

    def test_legacy_mount_counter_is_labelled_shared(self):
        j = self.sample()
        result = p.synthesize(j, 1010, None, 65 * p.GIB, True,
                              network_observed=2 * p.GIB, network_rate_ratio=.3)
        self.assertEqual(result["nfs_observed_bytes"], 2 * p.GIB)
        self.assertTrue(result["nfs_observation_is_shared"])
        self.assertGreater(result["network_remaining_estimate"], 10 * p.GIB)

    def test_incremental_does_not_fake_full_snapshot_total(self):
        j = self.sample()
        j["command"] += ["--parent", "/a"]
        result = p.synthesize(j, 1010, None, 80 * p.GIB, True)
        self.assertIsNone(result["stream_total_estimate"])
        self.assertIsNone(result["eta_seconds"])

    def test_retry_stream_counter_resets(self):
        j = self.sample()
        previous = p.synthesize(j, 1000, None, 65 * p.GIB, True)
        j.update(attempts=2, bytes_read=100)
        result = p.synthesize(j, 1010, previous, 65 * p.GIB, True)
        self.assertEqual(result["bytes_read"], 100)
        self.assertGreaterEqual(result["speed_bytes_s"], 0)

    def test_mountstats_selects_longest_nfs_match(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "mountstats"
            path.write_text(
                "device a mounted on /mnt/Cloud9 with fstype nfs4 statvers=1.1\n"
                " bytes: 0 0 0 0 0 123 0 0\n"
                "device b mounted on /mnt/Cloud9/backup-local with fstype nfs4 statvers=1.1\n"
                " bytes: 0 0 0 0 0 456 0 0\n")
            self.assertEqual(p.nfs_write_counter("/mnt/Cloud9/backup-local/Workstations", path), 456)

    def test_public_status_file_is_atomic_and_minimal(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "status"
            p.publish(1000, [{"bytes_read": 42, "state": "running"}], dest)
            obj = json.loads((dest / "1000.json").read_text())
            self.assertEqual(obj["jobs"][0]["bytes_read"], 42)
            self.assertEqual((dest / "1000.json").stat().st_mode & 0o777, 0o644)
            self.assertNotIn("command", obj["jobs"][0])


    def test_machine_progress_observer_sanitizes_journal(self):
        from subprocess import CompletedProcess
        unit = "harbor-machine-backup-a5d970db-9664-4be8-a0fb-bb1e93c60ec3.service"
        sample = dict(event="machine_progress", completed_members=3,
                      total_members=9, bytes_written=4 * p.GIB,
                      estimated_total_bytes=30 * p.GIB, eta_seconds=123,
                      command="do not expose", secret="should not publish")
        def fake_run(argv, **kwargs):
            if argv[:2] == ["systemctl", "list-units"]:
                return CompletedProcess(argv, 0, unit + " loaded active running\n", "")
            if argv[:2] == ["systemctl", "show"]:
                return CompletedProcess(argv, 0, "HARBOR_OWNER_UID=1000", "")
            if argv[0] == "journalctl":
                return CompletedProcess(argv, 0, json.dumps(sample) + "\n", "")
            raise AssertionError(argv)
        with patch.object(p.subprocess, "run", side_effect=fake_run):
            result = p.machine_live_status()
        self.assertIn(1000, result)
        self.assertEqual(result[1000]["completed_members"], 3)
        self.assertEqual(result[1000]["eta_seconds"], 123)
        self.assertNotIn("command", result[1000])
        self.assertNotIn("secret", result[1000])
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "status"
            p.publish(1000, [], dest, machine=result[1000])
            doc = json.loads((dest / "1000.json").read_text())
            self.assertEqual(doc["machine_backup"]["eta_seconds"], 123)
            self.assertNotIn("command", doc["machine_backup"])

    def test_machine_progress_observer_ignores_untrusted_unit(self):
        from subprocess import CompletedProcess
        with patch.object(p.subprocess, "run",
                          return_value=CompletedProcess([], 0,
                            "harbor-machine-backup-../untrusted.service loaded active running\n", "")):
            self.assertEqual(p.machine_live_status(), {})


if __name__ == "__main__":
    unittest.main()
