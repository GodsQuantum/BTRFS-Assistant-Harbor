"""One-click retry is idempotent, machine-scoped, and cannot cross exports."""
from __future__ import annotations
import unittest
import contextlib
import io
import json
from datetime import datetime, timedelta, timezone
from btrfs_backup_ng.cli.machine_set_v2 import (
    _select_unfinished_machine_backup, _machine_capture_stale, _result,
)

PROFILE = "118e0b70-dced-4a95-9179-8b45efbd3f51"
SET_ID = "b5d970db-9664-4be8-a0fb-bb1e93c60ec3"
OTHER = "a5d970db-9664-4be8-a0fb-bb1e93c60ec3"
MOUNT = {"device": 1, "mount": "/mnt/backup"}


class BackupButtonTest(unittest.TestCase):
    def item(self, **kwargs):
        return {"set_id": SET_ID, "profile_id": PROFILE,
                "machine_name": "Pegasus", "status": "sending",
                "destination_fingerprint": MOUNT, **kwargs}

    def test_resumes_exactly_one_incomplete_machine_backup(self):
        self.assertEqual(
            _select_unfinished_machine_backup([self.item()], PROFILE, "Pegasus", MOUNT),
            SET_ID)

    def test_new_date_after_completed_backup(self):
        record = self.item()
        record["status"] = "completed_btrfs_and_boot_files"
        self.assertIsNone(
            _select_unfinished_machine_backup([record], PROFILE, "Pegasus", MOUNT))

    def test_never_resume_other_machine(self):
        self.assertIsNone(
            _select_unfinished_machine_backup([self.item()], PROFILE, "Galactica", MOUNT))

    def test_changed_export_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "changed export"):
            _select_unfinished_machine_backup(
                [self.item()], PROFILE, "Pegasus", {"device": 999})

    def test_ambiguous_pending_sets_fail_closed(self):
        alt = self.item()
        alt["set_id"] = OTHER
        with self.assertRaisesRegex(ValueError, "multiple unfinished"):
            _select_unfinished_machine_backup(
                [self.item(), alt], PROFILE, "Pegasus", MOUNT)

    def test_old_partial_capture_must_not_mix_different_dates(self):
        now = datetime.now(timezone.utc)
        old = self.item()
        old["capture_started_utc"] = (now - timedelta(minutes=40)).isoformat()
        self.assertTrue(_machine_capture_stale(old, now))
        old["capture_completed_utc"] = (now - timedelta(minutes=39)).isoformat()
        self.assertFalse(_machine_capture_stale(old, now))

    def test_recent_interrupted_capture_can_resume_coherently(self):
        now = datetime.now(timezone.utc)
        row = self.item()
        row["capture_started_utc"] = (now - timedelta(seconds=35)).isoformat()
        self.assertFalse(_machine_capture_stale(row, now))

    def test_old_legacy_without_capture_marker_is_not_silently_abandoned(self):
        now = datetime.now(timezone.utc)
        self.assertFalse(_machine_capture_stale(self.item(), now))

    def test_success_report_includes_capture_identity_and_timestamp(self):
        item = {
            "archive": "machine20261023-dummy-000",
            "original_mount": "/home",
            "status": "completed",
            "snapshot_uuid": OTHER,
            "snapshot_created_utc": "2026-10-23T06:23:12+00:00",
        }
        data = {
            "set_id": SET_ID, "status": "completed_btrfs_only",
            "coverage": "btrfs-only", "members": [item], "boot_members": [],
            "capture_started_utc": "2026-10-23T06:23:10+00:00",
            "capture_completed_utc": "2026-10-23T06:23:13+00:00",
        }
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            self.assertEqual(_result(data), 0)
        result = json.loads(stream.getvalue())
        self.assertEqual(result["capture_completed_utc"],
                         data["capture_completed_utc"])
        self.assertEqual(result["members"][0]["snapshot_uuid"], OTHER)
        self.assertEqual(result["members"][0]["snapshot_created_utc"],
                         item["snapshot_created_utc"])
        self.assertFalse(result["bootable"])

    def test_no_pending_when_empty(self):
        self.assertIsNone(
            _select_unfinished_machine_backup([], PROFILE, "Pegasus", MOUNT))


if __name__ == "__main__":
    unittest.main()
