#include <QApplication>
#include "util/HarborProgress.h"
#include <QDir>
#include <QFile>
#include <QRegularExpression>
#include <QFileInfo>
#include <QIcon>
#include <QLockFile>
#include <QLocale>
#include <QMenu>
#include <QMessageBox>
#include <QProcess>
#include <QStandardPaths>
#include <QSystemTrayIcon>
#include <QTimer>
#include <QTextStream>
#include <QAction>
#include <unistd.h>

namespace {
QString label(const char *en, const char *fr, const char *zh) {
    const auto language = QLocale::system().language();
    return QString::fromUtf8(language == QLocale::French ? fr :
                             language == QLocale::Chinese ? zh : en);
}
bool activeMachineBackup() {
    // Keep detecting transient whole-computer units even when the observer
    // has been disabled or crashed, without requesting privileges.
    QProcess p;
    p.start(QStringLiteral("systemctl"), {
        QStringLiteral("list-units"), QStringLiteral("--no-legend"),
        QStringLiteral("--no-pager"), QStringLiteral("--plain"),
        QStringLiteral("--type=service"), QStringLiteral("--state=running"),
        QStringLiteral("harbor-machine-backup-*.service")});
    if (!p.waitForStarted(2000) || !p.waitForFinished(4000) ||
        p.exitStatus() != QProcess::NormalExit || p.exitCode() != 0)
        return false;
    for (const auto &line : QString::fromUtf8(p.readAllStandardOutput()).split(QLatin1Char('\n')))
        if (line.trimmed().startsWith(QStringLiteral("harbor-machine-backup-")) &&
            line.contains(QStringLiteral(".service"))) return true;
    return false;
}
bool harborWindowOpen() {
    // The GUI can be running via pkexec as root while the tray belongs to
    // the unprivileged KDE user. /proc/*/cmdline is readable across those
    // UIDs on standard Linux systems; never treat our tray/observer as GUI.
    const QDir proc(QStringLiteral("/proc"));
    for (const QString &entry : proc.entryList(QDir::Dirs | QDir::NoDotAndDotDot)) {
        bool numeric = false;
        entry.toULongLong(&numeric);
        if (!numeric) continue;
        QFile cmdline(proc.filePath(entry + QStringLiteral("/cmdline")));
        if (!cmdline.open(QIODevice::ReadOnly)) continue;
        const QByteArray firstArg = cmdline.read(512).split('\0').value(0);
        if (QFileInfo(QString::fromLocal8Bit(firstArg)).fileName()
            == QLatin1String("btrfs-assistant-harbor-bin"))
            return true;
    }
    return false;
}
bool trayNeeded(bool backupRunning, bool guiOpen) {
    return backupRunning && !guiOpen;
}
bool activeScheduledBackup() {
    // Scheduled backup profiles have UUID-based service names. Exclude
    // 'btrfs-assistant-harbor-progress.service' (always-on observer).
    QProcess p;
    p.start(QStringLiteral("systemctl"), {
        QStringLiteral("list-units"), QStringLiteral("--no-legend"),
        QStringLiteral("--no-pager"), QStringLiteral("--plain"),
        QStringLiteral("--type=service"), QStringLiteral("--state=running"),
        QStringLiteral("btrfs-assistant-harbor-*.service")});
    if (!p.waitForStarted(2000) || !p.waitForFinished(4000) ||
        p.exitStatus() != QProcess::NormalExit || p.exitCode() != 0)
        return false;
    static const QRegularExpression scheduled(
        QStringLiteral("^\\s*btrfs-assistant-harbor-[0-9a-f]{8}-"
                       "[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-"
                       "[0-9a-f]{12}\\.service\\s+"));
    for (const QString &line : QString::fromUtf8(p.readAllStandardOutput())
                                   .split(QLatin1Char('\n'))) {
        if (scheduled.match(line).hasMatch()) return true;
    }
    return false;
}
bool activeBackup() {
    QProcess p;
    p.start(QStringLiteral("systemctl"), {
        QStringLiteral("list-units"), QStringLiteral("--no-legend"),
        QStringLiteral("--no-pager"), QStringLiteral("--plain"),
        QStringLiteral("--type=service"), QStringLiteral("--state=running"),
        QStringLiteral("btrfs-assistant-harbor-job@*.service")});
    if (!p.waitForStarted(2000) || !p.waitForFinished(4000) ||
        p.exitStatus() != QProcess::NormalExit || p.exitCode() != 0)
        return false;
    for (const auto &line : QString::fromUtf8(p.readAllStandardOutput()).split(QLatin1Char('\n')))
        if (line.trimmed().startsWith(QStringLiteral("btrfs-assistant-harbor-job@")) &&
            line.contains(QStringLiteral(".service"))) return true;
    return false;
}
}
int main(int argc, char **argv) {
    QApplication app(argc, argv);
    app.setApplicationName(QStringLiteral("Btrfs Assistant Harbor Tray"));
    app.setQuitOnLastWindowClosed(false);
    const auto iconPath = QStringLiteral(
        "/usr/share/icons/hicolor/256x256/apps/btrfs-assistant-harbor.png");
    // The Harbor circle is part of our branded UX. Never resolve an older
    // third-party SVG theme icon before the packaged Harbor PNG.
    auto icon = QIcon(iconPath);
    if (icon.isNull()) icon = QIcon::fromTheme(QStringLiteral("btrfs-assistant-harbor"));
    if (app.arguments().contains(QStringLiteral("--self-test"))) {
        if (trayNeeded(false, false) || trayNeeded(false, true) ||
            trayNeeded(true, true) || !trayNeeded(true, false)) return 7;
        QTextStream(stdout) << "PASS_HARBOR_TRAY_QT_UNPRIVILEGED_AND_VISIBILITY\n";
        return 0;
    }
    if (app.arguments().contains(QStringLiteral("--status"))) {
        QTextStream(stdout) << ((activeBackup() || activeScheduledBackup() ||
            activeMachineBackup() || !HarborProgress::machine().isEmpty()) ? "running\n" : "idle\n");
        return 0;
    }
    if (app.arguments().size() != 1) return 2;
    if (geteuid() == 0) {
        QTextStream(stderr) << "Harbor tray requires the unprivileged user session\n";
        return 3;
    }
    const auto runtime = QStandardPaths::writableLocation(QStandardPaths::RuntimeLocation);
    if (runtime.isEmpty() || !QFileInfo(runtime).isDir()) return 4;
    QLockFile lock(QDir(runtime).filePath(QStringLiteral("btrfs-assistant-harbor-tray.lock")));
    lock.setStaleLockTime(0);
    if (!lock.tryLock(0)) return 0;

    QMenu menu;
    QSystemTrayIcon tray(icon);
    auto *open = menu.addAction(label("Open Harbor", "Ouvrir Harbor", "打开 Harbor"));
    auto *state = menu.addAction(QString());
    state->setEnabled(false);
    menu.addSeparator();
    auto *quit = menu.addAction(label("Hide icon (backup continues)",
        "Masquer l’icône (sauvegarde maintenue)", "隐藏图标（备份继续）"));
    auto update = [&] {
        const auto machine = HarborProgress::machine();
        const bool casRunning = activeBackup() || activeScheduledBackup() ||
                                !HarborProgress::active().isEmpty();
        const bool machineRunning = activeMachineBackup() || !machine.isEmpty();
        // Register with KDE only if the graphical Harbor window was closed
        // while a backup is really underway. Otherwise unregister the icon.
        const bool visible = trayNeeded(casRunning || machineRunning,
                                        harborWindowOpen());
        if (visible != tray.isVisible()) tray.setVisible(visible);
        const auto status = casRunning || machineRunning
            ? label("Backup in progress (systemd)", "Sauvegarde en cours (systemd)",
                    "备份进行中 (systemd)")
            : label("No active backup", "Aucune sauvegarde active",
                    "没有正在运行的备份");
        const QJsonObject stats = HarborProgress::active();
        if (!stats.isEmpty()) {
            state->setText(status + QStringLiteral(" — ") +
                           HarborProgress::size(stats.value(QStringLiteral("bytes_read")).toDouble()));
            tray.setToolTip(QStringLiteral("Btrfs Assistant Harbor\n") +
                            HarborProgress::overview(stats, true));
        } else if (!machine.isEmpty()) {
            const bool verifying = machine.value(QStringLiteral("phase")).toString()
                                   == QStringLiteral("verifying_archive");
            const auto phase = verifying
                ? label("Verifying backup integrity (no upload)",
                        "Vérification d’intégrité (aucun transfert)",
                        "正在校验备份完整性（无上传）")
                : status;
            state->setText(phase);
            tray.setToolTip(QStringLiteral("Btrfs Assistant Harbor\n") + phase +
                            QStringLiteral("\n") +
                            HarborProgress::machineOverview(machine, true));
        } else {
            state->setText(status + (machineRunning
                ? label(" (details unavailable)", " (détails indisponibles)",
                        "（详情暂不可用）") : QString()));
            tray.setToolTip(QStringLiteral("Btrfs Assistant Harbor — ") + status);
        }
    };
    QObject::connect(open, &QAction::triggered, &app, [] {
        if (!QProcess::startDetached(QStringLiteral("/usr/bin/btrfs-assistant-harbor-launcher")))
            QMessageBox::warning(nullptr, QStringLiteral("Harbor"),
                label("Could not open Harbor", "Impossible d'ouvrir Harbor", "无法打开 Harbor"));
    });
    QObject::connect(&tray, &QSystemTrayIcon::activated, &app,
        [open](QSystemTrayIcon::ActivationReason reason) {
            if (reason == QSystemTrayIcon::DoubleClick ||
                reason == QSystemTrayIcon::Trigger) open->trigger();
        });
    // The tray is never allowed to cancel a backup accidentally. Cancellation
    // remains in the application UI. A manual icon exit leaves systemd jobs on.
    QObject::connect(quit, &QAction::triggered, &app, [&] { app.quit(); });
    tray.setContextMenu(&menu);
    // Keep the observer resident but DO NOT register an always-visible icon.
    // update() registers it only for a background backup with a closed GUI.
    QTimer refresh;
    QObject::connect(&refresh, &QTimer::timeout, &app, update);
    refresh.start(2500);
    update();
    return app.exec();
}
