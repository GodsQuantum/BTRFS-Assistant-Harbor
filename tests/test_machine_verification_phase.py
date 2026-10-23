import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from btrfs_backup_ng.cli import machine_set_v2 as m
from btrfs_backup_ng.core.verify_v2 import VerificationResult

class VerificationStatusTests(unittest.TestCase):
    def test_real_final_archive_not_flagged_as_write_stall(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            members=[{"archive":"fixture","status":"sending","original_mount":"/"}]
            with patch.object(m,"forecast_machine",return_value={}):
                first=m._machine_progress_measure(root,{"members":members})
                self.assertEqual(first["phase"],"transferring")
                (root/"fixture.btrfs.zst").write_bytes(b"archive")
                second=m._machine_progress_measure(root,{"members":members})
                self.assertEqual(second["phase"],"verifying_archive")

    def test_checksum_diagnostic_preserves_reason(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            self.assertEqual(m._archive_verdict(root,"fixture").status,"incomplete")
            (root/"fixture.btrfs.zst").write_bytes(b"a")
            (root/"fixture.btrfs.zst.meta").write_bytes(b"b")
            with patch.object(m,"verify_checkpoint_index",
                             return_value=VerificationResult("corrupt","whole stream checksum mismatch")):
                self.assertEqual(m._archive_verdict(root,"fixture").detail,
                                 "whole stream checksum mismatch")
if __name__=="__main__":
    unittest.main()
