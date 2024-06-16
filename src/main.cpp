#include "ui/Cli.h"
#include "ui/MainWindow.h"
#include "util/BtrfsMaintenance.h"
#include "util/Settings.h"
#include "util/System.h"

#include <QApplication>
#include <QCommandLineParser>
#include <QDebug>
#include <QFile>
#include <QTranslator>

void setApplicationInfo()
{
    QCoreApplication::setApplicationName(QCoreApplication::translate("main", "Btrfs Assistant"));
    QCoreApplication::setApplicationVersion("2.1.1");
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

    // Ensure we are running on a system with btrfs
    if (!System::runCmd("findmnt --real -no fstype ", false).output.contains("btrfs")) {
        QTextStream(stderr) << QCoreApplication::translate("main", "Error: No Btrfs filesystems found") << Qt::endl;
        return 1;
    }

    // The btrfs object is used to interact with the application
    Btrfs btrfs;

    // If Snapper is installed, instantiate the snapper object
    Snapper *snapper = nullptr;
    if (QFile::exists(snapperPath)) {
        snapper = new Snapper(&btrfs, snapperPath);
    }

    // If $DISPLAY or $WAYLAND_DISPLAY is not empty, launch in GUI mode; else launch in CLI mode
    if (!qEnvironmentVariableIsEmpty("DISPLAY") || !qEnvironmentVariableIsEmpty("WAYLAND_DISPLAY")) {
        qDebug() << "DISPLAY / WAYLAND_DISPLAY variable is set, launching in GUI mode";
        QApplication app(argc, argv);

        app.setWindowIcon(QIcon(":/icons/btrfs-assistant.svg"));

        QTranslator translator;
        if (!translator.load("btrfsassistant_" + QLocale::system().name(), "/usr/share/btrfs-assistant/translations")) {
            QTextStream(stdout) << QCoreApplication::translate("main", "Warning: No translations available") << Qt::endl;
            ;
        }
        app.installTranslator(&translator);

        setApplicationInfo();

        // Process CLI options
        parser.process(app);
        if (parser.isSet(listOption) && snapper != nullptr) {
            return Cli::listSnapshots(snapper);
        } else if (parser.isSet(restoreOption) && snapper != nullptr) {
            return Cli::restore(&btrfs, snapper, parser.value(restoreOption).toInt());
        }

        // Set the desktop name for Wayland
        QGuiApplication::setDesktopFileName("btrfs-assistant");

        // If Btrfs Maintenance is installed, instantiate the btrfsMaintenance object
        std::unique_ptr<BtrfsMaintenance> btrfsMaintenance;
        if (QFile::exists(btrfsMaintenanceConfig)) {
            btrfsMaintenance.reset(new BtrfsMaintenance(btrfsMaintenanceConfig));
        }

        MainWindow mainWindow(&btrfs, btrfsMaintenance.get(), snapper);
        mainWindow.show();
        return app.exec();
    } else {
        QCoreApplication app(argc, argv);

        setApplicationInfo();

        parser.process(app);
        if (parser.isSet(listOption) && snapper != nullptr) {
            return Cli::listSnapshots(snapper);
        } else if (parser.isSet(restoreOption) && snapper != nullptr) {
            return Cli::restore(&btrfs, snapper, parser.value(restoreOption).toInt());
        } else {
            parser.showHelp();
            return 0;
        }
    }
}
