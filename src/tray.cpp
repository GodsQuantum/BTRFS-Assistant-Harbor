#include <QApplication>
#include "util/HarborProgress.h"
#include <QDir>
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
        QTextStream(stdout) << "PASS_HARBOR_TRAY_QT_UNPRIVILEGED\n";
        return 0;
    }
    if (app.arguments().contains(QStringLiteral("--status"))) {
        QTextStream(stdout) << ((activeBackup() || activeMachineBackup() || !HarborProgress::machine().isEmpty()) ? "running\n" : "idle\n");
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
    auto *quit = menu.addAction(label("Quit tray and stop backups",
        "Quitter Harbor et arrêter les sauvegardes", "退出托盘并停止备份"));
    auto update = [&] {
        const auto machine = HarborProgress::machine();
        const bool casRunning = activeBackup();
        const bool machineRunning = activeMachineBackup() || !machine.isEmpty();
        const auto status = casRunning || machineRunning
            ? label("Backup in progress (systemd)", "Sauvegarde en cours (systemd)",
                    "备份进行中 (systemd)")
            : label("No active backup", "Aucune sauvegarde active",
                    "没有正在运行的备份");
        quit->setText(machineRunning && !casRunning
            ? label("Close tray (backup continues)",
                    "Fermer l’icône (la sauvegarde continue)",
                    "关闭托盘（备份继续运行）")
            : label("Quit tray and stop backups",
                    "Quitter Harbor et arrêter les sauvegardes",
                    "退出托盘并停止备份"));
        const QJsonObject stats = HarborProgress::active();
        if (!stats.isEmpty()) {
            state->setText(status + QStringLiteral(" — ") +
                           HarborProgress::size(stats.value(QStringLiteral("bytes_read")).toDouble()));
            tray.setToolTip(QStringLiteral("Btrfs Assistant Harbor\n") +
                            HarborProgress::overview(stats, true));
        } else if (!machine.isEmpty()) {
            state->setText(status);
            tray.setToolTip(QStringLiteral("Btrfs Assistant Harbor\n") +
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
    QObject::connect(quit, &QAction::triggered, &app, [&] {
        if (!activeBackup()) { app.quit(); return; }
        if (QMessageBox::question(nullptr, QStringLiteral("Harbor"), label(
                "Stop running backups and quit tray? Verified CAS data is retained.",
                "Arrêter les sauvegardes et quitter ? Les données CAS vérifiées sont conservées.",
                "停止当前备份并退出？已验证 CAS 数据保留。"))
            != QMessageBox::Yes) return;
        quit->setEnabled(false);
        auto *stop = new QProcess(&app);
        QObject::connect(stop, qOverload<int, QProcess::ExitStatus>(&QProcess::finished),
            &app, [&, stop](int code, QProcess::ExitStatus status) {
                stop->deleteLater();
                if (status == QProcess::NormalExit && code == 0 && !activeBackup())
                    app.quit();
                else {
                    quit->setEnabled(true);
                    QMessageBox::warning(nullptr, QStringLiteral("Harbor"), label(
                        "Backup cancellation failed. Tray remains running.",
                        "Échec de l'arrêt de la sauvegarde. Harbor reste actif.",
                        "备份停止失败，托盘仍在运行。"));
                }
            });
        QObject::connect(stop, &QProcess::errorOccurred, &app,
            [&, stop](QProcess::ProcessError error) {
                if (error != QProcess::FailedToStart) return;
                quit->setEnabled(true);
                stop->deleteLater();
                QMessageBox::warning(nullptr, QStringLiteral("Harbor"), label(
                    "Could not ask for administrator permission.",
                    "Impossible de demander l'autorisation administrateur.",
                    "无法请求管理员授权。"));
            });
        stop->start(QStringLiteral("pkexec"),
                    {QStringLiteral("/usr/bin/btrfs-assistant-harbor-tray-stop")});
    });
    tray.setContextMenu(&menu);
    tray.show(); // Qt registers when the KDE StatusNotifierWatcher becomes available.
    QTimer refresh;
    QObject::connect(&refresh, &QTimer::timeout, &app, update);
    refresh.start(5000);
    update();
    return app.exec();
}
