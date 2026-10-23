from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class BrandContract(unittest.TestCase):
    def test_icon_sizes(self):
        self.assertIn("foreach(harbor_size",(ROOT/"icons/CMakeLists.txt").read_text())
        for n in (16,24,32,48,64,128,256,512):
            image=ROOT/f"icons/hicolor/harbor-icon-{n}.png"
            self.assertTrue(image.is_file())
            self.assertGreater(image.stat().st_size,400)
    def test_readme(self):
        for lang in ("README.md","README.fr.md","README.zh-CN.md"):
            self.assertIn("branding/harbor-banner.png",(ROOT/lang).read_text())
        self.assertIn("harbor-icon-256.png",(ROOT/"src/main.cpp").read_text())
    def test_native(self):
        self.assertIn('cp packaging/arch/btrfs-assistant-harbor.install',(ROOT/".github/workflows/native-packages.yml").read_text())
        self.assertIn('/usr/share/icons/hicolor/*/apps/btrfs-assistant-harbor.png',(ROOT/"packaging/fedora/btrfs-assistant-harbor.spec").read_text())
if __name__=="__main__":
    unittest.main()
