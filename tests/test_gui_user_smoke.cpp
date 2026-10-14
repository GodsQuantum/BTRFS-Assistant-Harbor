#include <QtTest/QtTest>
#include <QApplication>
#include <QComboBox>
#include <QLineEdit>
#include <QListWidget>
#include <QPlainTextEdit>
#include <QProcess>
#include <QPushButton>
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
