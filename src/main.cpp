#include "ui/Cli.h"
#include "ui/MainWindow.h"
#include "ui/HarborLanguage.h"
#include "util/BtrfsMaintenance.h"
#include "util/Settings.h"
#include "util/System.h"

#include <QApplication>
#include <QCommandLineParser>
#include <QDebug>
#include <QFile>
#include <QTranslator>
#include <QSystemTrayIcon>
#include <QMenu>
#include <QProcess>
#include <QMessageBox>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>

#include <optional>

void setApplicationInfo()
{
    QCoreApplication::setApplicationName(QCoreApplication::translate("main", "Btrfs Assistant Harbor"));
    QCoreApplication::setApplicationVersion("0.1.4");
}

int main(int argc, char *argv[])
{
    QCommandLineParser parser;
    parser.setApplicationDescription(QCoreApplication::translate("main", "An application for managing Btrfs and Snapper"));
    parser.addHelpOption();
    parser.addVersionOption();

    QCommandLineOption listOption(QStringList() << "l"
                                                << "list",
                                  QCoreApplication::translate("main", "List snapshots"));
    parser.addOption(listOption);

    QCommandLineOption restoreOption(QStringList() << "r"
                                                   << "restore",
                                     QCoreApplication::translate("main", "Restore the given snapshot"),
                                     QCoreApplication::translate("main", "index of snapshot"));
    parser.addOption(restoreOption);

    QString snapperPath = Settings::instance().value("snapper", "/usr/bin/snapper").toString();
    QString btrfsMaintenanceConfig = Settings::instance().value("bm_config", "/etc/default/btrfsmaintenance").toString();

    // The btrfs object is used to interact with the application. Constructing it walks every
    // subvolume of every mounted Btrfs filesystem, so it is only created once the command line
    // has been processed: --help and --version have no use for it and answer without privileges.
    std::optional<Btrfs> btrfs;
    Snapper *snapper = nullptr;

    auto initializeBtrfs = [&]() {
        // Ensure we are running on a system with btrfs
        if (!System::runCmd("findmnt", {"--real", "-no", "fstype"}, false).output.contains("btrfs")) {
            QTextStream(stderr) << QCoreApplication::translate("main", "Error: No Btrfs filesystems found") << Qt::endl;
            return false;
        }

        btrfs.emplace();

        // If Snapper is installed, instantiate the snapper object
        if (QFile::exists(snapperPath)) {
            snapper = new Snapper(&btrfs.value(), snapperPath);
        }

        return true;
    };

    // If $DISPLAY or $WAYLAND_DISPLAY is not empty, launch in GUI mode; else launch in CLI mode
    if (!qEnvironmentVariableIsEmpty("DISPLAY") || !qEnvironmentVariableIsEmpty("WAYLAND_DISPLAY")) {
        qDebug() << "DISPLAY / WAYLAND_DISPLAY variable is set, launching in GUI mode";
        QApplication app(argc, argv);

        app.setWindowIcon(QIcon(":/icons/btrfs-assistant-harbor.svg"));

        QTranslator translator;
        const QString language = HarborLanguage::selected();
        if (language != QLatin1String("en_US")) {
            if (HarborLanguage::loadCatalog(translator, language,
                    QStringLiteral("/usr/share/btrfs-assistant-harbor/translations"))) {
                app.installTranslator(&translator);
            } else {
                QTextStream(stderr) << "Warning: requested Harbor translation is unavailable: "
                                    << language << Qt::endl;
            }
        }

        setApplicationInfo();

        // Process CLI options
        parser.process(app);

        if (!initializeBtrfs()) {
            return 1;
        }

        if (parser.isSet(listOption) && snapper != nullptr) {
            return Cli::listSnapshots(snapper);
        } else if (parser.isSet(restoreOption) && snapper != nullptr) {
            return Cli::restore(&btrfs.value(), snapper, parser.value(restoreOption).toInt());
        }

        // Set the desktop name for Wayland
        QGuiApplication::setDesktopFileName("btrfs-assistant-harbor");

        // If Btrfs Maintenance is installed, instantiate the btrfsMaintenance object
        std::unique_ptr<BtrfsMaintenance> btrfsMaintenance;
        if (QFile::exists(btrfsMaintenanceConfig)) {
            btrfsMaintenance.reset(new BtrfsMaintenance(btrfsMaintenanceConfig));
        }

        MainWindow mainWindow(&btrfs.value(), btrfsMaintenance.get(), snapper);
        // The tray is only a controller. Persistent manual transfers live in
        // systemd, so a GUI crash still cannot kill a Btrfs send.
        std::unique_ptr<QSystemTrayIcon> tray;
        std::unique_ptr<QMenu> trayMenu;
        // pkexec processes do not own the user's KDE D-Bus tray session.
        if (qEnvironmentVariableIsEmpty("PKEXEC_UID") &&
            QSystemTrayIcon::isSystemTrayAvailable()) {
            app.setQuitOnLastWindowClosed(false);
            tray = std::make_unique<QSystemTrayIcon>(app.windowIcon(), &app);
            trayMenu = std::make_unique<QMenu>(&mainWindow);
            const auto *showAction = trayMenu->addAction(
                QCoreApplication::translate("main", "Show Harbor"));
            const auto *quitAction = trayMenu->addAction(
                QCoreApplication::translate("main", "Quit Harbor and stop manual backups"));
            QObject::connect(showAction, &QAction::triggered, &mainWindow, [&mainWindow] {
                mainWindow.showNormal();
                mainWindow.raise();
                mainWindow.activateWindow();
            });
            QObject::connect(tray.get(), &QSystemTrayIcon::activated, &mainWindow,
                [&mainWindow](QSystemTrayIcon::ActivationReason reason) {
                    if (reason == QSystemTrayIcon::DoubleClick ||
                        reason == QSystemTrayIcon::Trigger) {
                        mainWindow.showNormal();
                        mainWindow.raise();
                        mainWindow.activateWindow();
                    }
                });
            QObject::connect(quitAction, &QAction::triggered, &app, [&app, &mainWindow] {
                const auto answer = QMessageBox::question(&mainWindow,
                    QCoreApplication::translate("main", "Quit Harbor"),
                    QCoreApplication::translate("main",
                        "Quit Harbor and stop any running manual backup? "
                        "Existing completed CAS objects will be retained."));
                if (answer != QMessageBox::Yes) return;
                QProcess controller;
                controller.start(QStringLiteral("/usr/bin/btrfs-assistant-harbor-job"),
                                 {QStringLiteral("cancel-all")});
                if (!controller.waitForFinished(45000) || controller.exitStatus() != QProcess::NormalExit ||
                    controller.exitCode() != 0) {
                    QMessageBox::warning(&mainWindow,
                        QCoreApplication::translate("main", "Backup still running"),
                        QCoreApplication::translate("main",
                            "Harbor could not stop the background job. The application stays open."));
                    mainWindow.showNormal();
                    return;
                }
                app.quit();
            });
            tray->setContextMenu(trayMenu.get());
            tray->setToolTip(QCoreApplication::translate("main", "Btrfs Assistant Harbor"));
            tray->show();
        }
        mainWindow.show();
        return app.exec();
    } else {
        QCoreApplication app(argc, argv);

        setApplicationInfo();

        parser.process(app);

        // Nothing to do but print the usage; there is no reason to look at the filesystem first
        if (!parser.isSet(listOption) && !parser.isSet(restoreOption)) {
            parser.showHelp();
            return 0;
        }

        if (!initializeBtrfs()) {
            return 1;
        }

        if (parser.isSet(listOption) && snapper != nullptr) {
            return Cli::listSnapshots(snapper);
        } else if (parser.isSet(restoreOption) && snapper != nullptr) {
            return Cli::restore(&btrfs.value(), snapper, parser.value(restoreOption).toInt());
        } else {
            parser.showHelp();
            return 0;
        }
    }
}
