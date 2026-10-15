"""ESP tar preflight: safe relative paths, fail closed on links and traversal."""
from __future__ import annotations
import io
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

HOOK = Path(__file__).resolve().parents[1] / "backend/recovery/harbor-validate-esp-tar"


class EspTarSafety(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="harbor-esp-tar-")
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def make(self, names, kind=None):
        tarpath = self.dir / "esp.tar.gz"
        with tarfile.open(tarpath, "w:gz") as tf:
            for n in names:
                entry = tarfile.TarInfo(n)
                entry.size = 1
                entry.type = tarfile.REGTYPE
                if n.endswith("/"):
                    entry.type, entry.size = tarfile.DIRTYPE, 0
                if kind == "symlink":
                    entry.type, entry.size, entry.linkname = tarfile.SYMTYPE, 0, "../../out"
                if kind == "hardlink":
                    entry.type, entry.size, entry.linkname = tarfile.LNKTYPE, 0, "../../out"
                tf.addfile(entry, io.BytesIO(b"x") if entry.size else None)
        return tarpath

    def check(self, items, kind=None):
        archive = self.make(items, kind)
        return subprocess.run(["bash", str(HOOK), str(archive)], capture_output=True, text=True)

    def test_normal_gnu_tar_dot_prefix_is_accepted(self):
        r = self.check(["./", "./EFI/", "./EFI/debian/", "./EFI/debian/grubx64.efi",
                        "./EFI/BOOT/", "./EFI/BOOT/BOOTX64.EFI"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("HARBOR_ESP_ARCHIVE_PATHS_VERIFIED", r.stdout)

    def test_parent_directory_traversal_rejected(self):
        self.assertEqual(self.check(["./EFI/../../etc/passwd"]).returncode, 72)

    def test_absolute_path_rejected(self):
        self.assertEqual(self.check(["/etc/passwd"]).returncode, 72)

    def test_symlink_rejected(self):
        self.assertEqual(self.check(["./EFI/boot/link"], "symlink").returncode, 72)

    def test_hardlink_rejected(self):
        self.assertEqual(self.check(["./EFI/boot/link"], "hardlink").returncode, 72)

    def test_weird_path_rejected(self):
        self.assertEqual(self.check(["./EFI/path with spaces"]).returncode, 72)

    def test_backslash_rejected(self):
        self.assertEqual(self.check(["./EFI/..\\windows"]).returncode, 72)

    def test_empty_dir_only_rejected(self):
        self.assertEqual(self.check(["./"]).returncode, 72)


if __name__ == "__main__":
    unittest.main()
