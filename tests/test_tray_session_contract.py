"""No backup is launched or cancelled during these source-level safety tests."""
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
class TraySessionContract(unittest.TestCase):
    def test_unprivileged_session_before_root_gui(self):
        script = (ROOT / "src/btrfs-assistant-harbor-launcher").read_text()
        self.assertLess(script.index("systemctl --user start btrfs-assistant-harbor-tray.service"),
                        script.index('exec pkexec'))
        tray = (ROOT / "src/tray.cpp").read_text()
        self.assertIn("geteuid() == 0", tray)
        self.assertIn("QLockFile lock(", tray)
        self.assertIn("Hide icon (backup continues)", tray)
        self.assertIn("trayNeeded(casRunning || machineRunning,", tray)
        self.assertIn("harborWindowOpen()", tray)
        self.assertIn("tray.setVisible(visible)", tray)
        self.assertNotIn("tray.show();", tray)
        self.assertIn("activeScheduledBackup()", tray)
        self.assertIn("No active backup", tray)
        self.assertIn("HarborProgress::machine()", tray)
        self.assertIn("HarborProgress::machineOverview", tray)
        self.assertIn("activeMachineBackup()", tray)
        self.assertIn("harbor-machine-backup-*.service", tray)
        self.assertIn("if (visible != tray.isVisible())", tray)
        self.assertIn("details unavailable", tray)
        progress=(ROOT/"src/util/HarborProgress.h").read_text()
        self.assertNotIn("calcul / pause",progress)
        self.assertIn("Vérification d’intégrité (durée inconnue)",progress)
        self.assertIn("Temps restant indisponible (travail en cours)",progress)
    def test_tray_has_fixed_polkit_stop_only(self):
        policy = (ROOT / "src/org.btrfs-assistant-harbor.pkexec.policy").read_text()
        self.assertIn("/usr/bin/btrfs-assistant-harbor-tray-stop", policy)
        stop = (ROOT / "backend/harbor-tray-stop").read_text()
        self.assertIn("PKEXEC_UID", stop)
        self.assertIn("exec /usr/bin/btrfs-assistant-harbor-job cancel-all", stop)
        self.assertNotIn('"$@"', stop)
    def test_no_autostart_backup(self):
        unit = (ROOT / "packaging/systemd/btrfs-assistant-harbor-tray.service").read_text()
        self.assertIn("ExecStart=/usr/bin/btrfs-assistant-harbor-tray", unit)
        self.assertNotIn("btrfs send", unit)
        self.assertNotIn("harbor-transport send", unit)
        self.assertIn("WantedBy=default.target", unit)
