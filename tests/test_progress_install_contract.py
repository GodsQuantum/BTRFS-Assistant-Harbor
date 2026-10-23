from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]

class ProgressInstallContract(unittest.TestCase):
    def test_observer_works_without_prior_legacy_jobs(self):
        unit=(ROOT/"packaging/systemd/btrfs-assistant-harbor-progress.service").read_text()
        self.assertNotIn("ConditionPathExists=",unit)
        self.assertIn("WantedBy=multi-user.target",unit)
        self.assertIn("NoNewPrivileges=yes",unit)
    def test_arch_observer_enabled_without_auto_backups(self):
        pkg=(ROOT/"packaging/arch/PKGBUILD.in").read_text()
        hook=(ROOT/"packaging/arch/btrfs-assistant-harbor.install").read_text()
        self.assertIn("install='btrfs-assistant-harbor.install'",pkg)
        self.assertIn("systemctl enable --now btrfs-assistant-harbor-progress.service",hook)
        self.assertIn("post_install()",hook)
        self.assertIn("post_upgrade()",hook)
        self.assertNotIn("systemctl enable --now harbor-machine-backup",hook)
    def test_debian_package_runs_readonly_observer_only(self):
        source=(ROOT/"packaging/debian/build_preview.py").read_text()
        hook=(ROOT/"packaging/debian/postinst").read_text()
        remove=(ROOT/"packaging/debian/postrm").read_text()
        self.assertIn('("postinst", "postrm")',source)
        self.assertIn("systemctl enable --now btrfs-assistant-harbor-progress.service",hook)
        self.assertIn("systemctl disable --now btrfs-assistant-harbor-progress.service",remove)
        self.assertNotIn("systemctl stop harbor-machine-backup",remove)
        self.assertNotIn("systemctl start harbor-machine-backup",hook)
    def test_fedora_enable_progress(self):
        spec=(ROOT/"packaging/fedora/btrfs-assistant-harbor.spec").read_text()
        self.assertIn("systemctl enable --now btrfs-assistant-harbor-progress.service",spec)
        self.assertNotIn("systemctl enable --now harbor-machine-backup",spec)
if __name__=="__main__":
    unittest.main()
