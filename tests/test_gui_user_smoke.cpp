#include <QtTest/QtTest>
#include <QApplication>
#include <QComboBox>
#include <QLineEdit>
#include <QListWidget>
#include <QPlainTextEdit>
#include <QProcess>
#include <QPushButton>
#include <QTranslator>
#include <QMainWindow>
#include <QScrollArea>
#include <QScrollBar>
#include <QTabBar>
#include <QTabWidget>
#include "ui_MainWindow.h"
#include "model/SubvolModel.h"
#include "ui/RemoteBackupWidget.h"
class HarborGuiUserSmoke : public QObject {
    Q_OBJECT
    static QPushButton *button(RemoteBackupWidget &w, const QString &label) {
        for (auto *b : w.findChildren<QPushButton*>())
            if (b->text() == label) return b;
        return nullptr;
    }
    static QComboBox *backend(RemoteBackupWidget &w) {
        for (auto *c : w.findChildren<QComboBox*>())
            if (c->count() == 2 && c->itemData(0).toString() == "legacy" &&
                c->itemData(1).toString() == "cas") return c;
        return nullptr;
    }
private slots:
    void opensWithoutAnyUserConfiguration() {
        RemoteBackupWidget w(nullptr);
        w.resize(1200, 1000);
        w.show();
        QApplication::processEvents();
        QVERIFY(w.isVisible());
        QVERIFY(backend(w));
        QCOMPARE(backend(w)->currentData().toString(), QString("legacy"));
        QVERIFY(w.findChildren<QListWidget*>().size() >= 2);
        QCOMPARE(w.findChildren<QPlainTextEdit*>().size(), 1);
    }
    void switchingEnginesUpdatesEnabledActions() {
        RemoteBackupWidget w(nullptr);
        auto *c = backend(w);
        QVERIFY(c);
        auto *init = button(w, "Initialize CAS destination");
        auto *del = button(w, "Delete selected CAS backup");
        auto *sweep = button(w, "Reclaim unused CAS chunks");
        auto *resume = button(w, "Resume selected");
        auto *interrupted = button(w, "Interrupted transfers");
        QVERIFY(init && del && sweep && resume && interrupted);
        QVERIFY(!init->isEnabled() && !del->isEnabled() && !sweep->isEnabled());
        QVERIFY(resume->isEnabled() && interrupted->isEnabled());
        c->setCurrentIndex(1);
        QApplication::processEvents();
        QVERIFY(init->isEnabled() && del->isEnabled() && sweep->isEnabled());
        QVERIFY(!resume->isEnabled() && !interrupted->isEnabled());
        c->setCurrentIndex(0);
        QApplication::processEvents();
        QVERIFY(!del->isEnabled() && !sweep->isEnabled() && resume->isEnabled());
    }
    void workflowsAreAvailableToUser() {
        RemoteBackupWidget w(nullptr);
        for (const auto &text : QStringList{
             "Send selected snapshot", "List remote backups",
             "Verify selected archive", "Preview recovery",
             "Enable schedule", "Disable schedule", "Scheduled backups",
             "Audit backup coverage", "List machine backup sets",
             "Preview staged machine restore", "Refresh snapshots"}) {
            QVERIFY2(button(w, text), qPrintable(text));
        }
        bool destination=false, staging=false;
        for (auto *line : w.findChildren<QLineEdit*>()) {
            destination |= line->placeholderText().contains("NFS/SMB");
            staging |= line->placeholderText().contains("Btrfs staging");
        }
        QVERIFY(destination && staging);
    }
    void frenchUiAndReadOnlyStatusAreConsistent() {
        QTranslator translator;
        const QString qm = QCoreApplication::applicationDirPath()
                           + "/btrfsassistant_fr_FR.qm";
        QVERIFY2(translator.load(qm), qPrintable(qm));
        QCoreApplication::installTranslator(&translator);
        QCOMPARE(QCoreApplication::translate("MainWindow", "Remote backups"),
                 QStringLiteral("Sauvegardes distantes"));
        QCOMPARE(QCoreApplication::translate("MainWindow", "Filter..."),
                 QString::fromUtf8("Filtrer…"));
        QCOMPARE(QCoreApplication::translate("RemoteBackupWidget",
                 "Confirm destructive CAS cleanup"),
                 QStringLiteral("Confirmer la purge destructive du dépôt CAS"));
        SubvolumeModel model;
        Subvolume subvol;
        subvol.id = 256;
        subvol.flags = 1;
        model.addSubvolume(subvol);
        auto pos = model.index(0, SubvolumeModel::ReadOnly);
        QCOMPARE(model.data(pos, Qt::DisplayRole).toString(), QStringLiteral("Oui"));
        QCOMPARE(model.data(pos, SubvolumeModel::Sort).toBool(), true);
        subvol.flags = 0;
        model.updateSubvolume(subvol);
        QCOMPARE(model.data(pos, Qt::DisplayRole).toString(), QStringLiteral("Non"));
        QCOMPARE(model.data(pos, SubvolumeModel::Sort).toBool(), false);
        QCoreApplication::removeTranslator(&translator);
    }
    void remoteTabIsMouseNavigableAtRealWindowWidth() {
        QMainWindow host;
        Ui::MainWindow ui;
        ui.setupUi(&host);
        host.resize(946, 717);
        auto *backupScroll = new QScrollArea;
        backupScroll->setWidgetResizable(true);
        backupScroll->setWidget(new RemoteBackupWidget(nullptr));
        auto *tabs = ui.tabWidget_mainWindow;
        const int remoteIndex = tabs->addTab(backupScroll, "Sauvegardes distantes");
        tabs->setTabVisible(tabs->indexOf(ui.tab_btrfsmaintenance), false);
        tabs->setCurrentIndex(0);
        host.show();
        QApplication::processEvents();
        auto *bar = tabs->tabBar();
        QVERIFY(bar->isVisible());
        QVERIFY(bar->isTabEnabled(remoteIndex));
        const QRect rect = bar->tabRect(remoteIndex);
        QVERIFY(rect.width() > 60);
        QVERIFY(rect.right() <= bar->width());
        QTest::mouseClick(bar, Qt::LeftButton, Qt::NoModifier, rect.center());
        QTRY_COMPARE(tabs->currentIndex(), remoteIndex);
        QVERIFY(backupScroll->isVisible());
    }
    void remoteBackupScrollableWithRealFrenchLayout() {
        QTranslator translator;
        const QString qm = QCoreApplication::applicationDirPath()
                           + "/btrfsassistant_fr_FR.qm";
        QVERIFY(translator.load(qm));
        QCoreApplication::installTranslator(&translator);
        QScrollArea area;
        area.setWidgetResizable(true);
        area.setWidget(new RemoteBackupWidget(nullptr));
        area.resize(946, 717);
        area.show();
        QApplication::processEvents();
        QVERIFY(area.widget()->isVisible());
        QVERIFY(area.verticalScrollBar()->maximum() > 0);
        const QString output = qEnvironmentVariable("HARBOR_GUI_QA_SHOTS");
        if (!output.isEmpty()) {
            QVERIFY(area.grab().save(output + "/remote-top.png"));
            area.verticalScrollBar()->setValue(area.verticalScrollBar()->maximum());
            QApplication::processEvents();
            QVERIFY(area.grab().save(output + "/remote-bottom.png"));
        }
        QCoreApplication::removeTranslator(&translator);
    }
    void idleAppHasNoUnexpectedProcess() {
        RemoteBackupWidget w(nullptr);
        w.show();
        QApplication::processEvents();
        const auto children = w.findChildren<QProcess*>();
        QCOMPARE(children.size(), 1);
        QCOMPARE(children[0]->state(), QProcess::NotRunning);
        QVERIFY(w.findChildren<QPlainTextEdit*>()[0]->isReadOnly());
    }
};
QTEST_MAIN(HarborGuiUserSmoke)
#include "test_gui_user_smoke.moc"
