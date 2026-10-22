#include <QtTest/QtTest>
#include <QApplication>
#include <QAccessible>
#include <QTemporaryDir>
#include <QFile>
#include <QFileInfo>
#include <QDir>
#include <QDirIterator>
#include <QRandomGenerator>
#include <QElapsedTimer>
#include <QThread>
#include <QComboBox>
#include <QLineEdit>
#include <QSettings>
#include <QListWidget>
#include <QPlainTextEdit>
#include <QProcess>
#ifdef Q_OS_UNIX
#include <signal.h>
#endif
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
#include "ui/DiffViewer.h"
#include "util/Btrfs.h"
#include "util/Snapper.h"
#include "util/System.h"
class HarborGuiUserSmoke : public QObject {
    Q_OBJECT
    static QPushButton *button(RemoteBackupWidget &w, const QString &label) {
        for (auto *b : w.findChildren<QPushButton*>())
            if (b->text() == label) return b;
        return nullptr;
    }
#ifdef Q_OS_UNIX
    // PID 1 in a container can retain zombie descendants after SIGTERM.
    // Zombies cannot run or write but make kill(-pgid,0) look successful.
    static bool groupHasRunningMembers(pid_t pgid) {
#ifdef Q_OS_LINUX
        QDir proc(QStringLiteral("/proc"));
        for (const QString &entry : proc.entryList(QDir::Dirs | QDir::NoDotAndDotDot)) {
            bool numeric = false;
            entry.toLongLong(&numeric);
            if (!numeric) continue;
            QFile stat(QStringLiteral("/proc/") + entry + QStringLiteral("/stat"));
            if (!stat.open(QIODevice::ReadOnly)) continue;
            const QByteArray data = stat.readAll();
            const auto end = data.lastIndexOf(')');
            if (end < 0) continue;
            const auto fields = data.mid(end + 2).simplified().split(' ');
            if (fields.size() < 3) continue;
            bool valid = false;
            const auto foundGroup = fields.at(2).toLong(&valid);
            if (valid && foundGroup == pgid && fields.at(0) != "Z" && fields.at(0) != "X")
                return true;
        }
        return false;
#else
        return ::kill(-pgid, 0) == 0;
#endif
    }
#endif
    static QComboBox *backend(RemoteBackupWidget &w) {
        for (auto *c : w.findChildren<QComboBox*>())
            if (c->count() == 2 && c->itemData(0).toString() == "legacy" &&
                c->itemData(1).toString() == "cas") return c;
        return nullptr;
    }
private slots:
    // Produces honest screenshots of the *real Qt widget* in a disposable
    // headless environment; no fabricated connected archive or backup state.
    // Not executed unless explicitly requested by the documentation workflow.
    void captureRealQtBackupTabForDocumentation() {
        const QString dir = qEnvironmentVariable("HARBOR_DOC_SCREENSHOT_DIR");
        if (dir.isEmpty()) return;
        QVERIFY(QDir().mkpath(dir));
        RemoteBackupWidget widget(nullptr);
        widget.setWindowTitle(QStringLiteral("Btrfs Assistant Harbor — Remote backups"));
        widget.resize(1450, 1110);
        widget.show();
        QApplication::processEvents();
        auto *engine = backend(widget);
        QVERIFY(engine);
        engine->setCurrentIndex(1);
        QVERIFY(engine->itemText(1).contains(QStringLiteral("deduplicated")));
        for (auto *field : widget.findChildren<QLineEdit*>()) {
            if (field->toolTip().contains(QStringLiteral("Machine identity")))
                field->setText(QStringLiteral("Workstation"));
        }
        QApplication::processEvents();
        const QString path = QDir(dir).filePath(QStringLiteral("remote-backups-qt6.png"));
        QVERIFY2(widget.grab().save(path, "PNG"), qPrintable(path));
        QVERIFY2(QFileInfo(path).size() > 20000, "Screenshot did not render");
    }
    void commandExecutionFailsClosedOnTimeoutAndNoShellInterpretation() {
        const auto literal = System::runCmd(QStringLiteral("/usr/bin/printf"),
                                            {QStringLiteral("%s"), QStringLiteral("literal;$(exit 66)")},
                                            false, System::seconds(2));
        QCOMPARE(literal.exitCode, 0);
        QCOMPARE(literal.output, QStringLiteral("literal;$(exit 66)"));

        QElapsedTimer timer;
        timer.start();
        const auto timedOut = System::runCmd(QStringLiteral("/usr/bin/sleep"),
                                             {QStringLiteral("3")}, true,
                                             System::milliseconds(50));
        QVERIFY(timedOut.exitCode != 0);
        QVERIFY(timer.elapsed() < 2600);
        const auto missing = System::runCmd(QStringLiteral("/this/harbor/command/does/not/exist"),
                                            {}, true, System::milliseconds(100));
        QVERIFY(missing.exitCode != 0);
    }
    void nativeDiffViewerSnapshotDiscoveryHandlesUntrustedFilenames() {
        QTemporaryDir scratch;
        QVERIFY(scratch.isValid());
        const QString stem = scratch.filePath(QStringLiteral(".snapshots"));
        const QString strange = QStringLiteral("qa ; $(touch SHOULD_NOT_EXIST).txt");
        QVERIFY(QDir().mkpath(stem + QStringLiteral("/1/snapshot")));
        QVERIFY(QDir().mkpath(stem + QStringLiteral("/2/snapshot")));
        QVERIFY(QDir().mkpath(stem + QStringLiteral("/non_numeric/snapshot")));
        QVERIFY(QDir().mkpath(stem + QStringLiteral("/3/snapshot")));
        const QString first = stem + QStringLiteral("/1/snapshot/") + strange;
        const QString second = stem + QStringLiteral("/2/snapshot/") + strange;
        const QString bogus = stem + QStringLiteral("/non_numeric/snapshot/") + strange;
        for (const auto &name : {first, second, bogus}) {
            QFile file(name);
            QVERIFY(file.open(QIODevice::WriteOnly));
            QCOMPARE(file.write("snapshot test", 13), qint64(13));
        }
        const QString outside = scratch.filePath(QStringLiteral("outside.txt"));
        {
            QFile file(outside);
            QVERIFY(file.open(QIODevice::WriteOnly));
            QCOMPARE(file.write("outside", 7), qint64(7));
        }
        QVERIFY(QFile::link(outside, stem + QStringLiteral("/3/snapshot/") + strange));
        const auto files = DiffViewer::snapshotFileCandidates(stem + QStringLiteral("/1/snapshot"), first);
        QCOMPARE(files.size(), 2);
        QVERIFY(files.contains(first));
        QVERIFY(files.contains(second));
        QVERIFY(!files.contains(bogus));
        QVERIFY(!QFileInfo::exists(scratch.filePath(QStringLiteral("SHOULD_NOT_EXIST"))));
        QVERIFY(DiffViewer::snapshotFileCandidates(stem + QStringLiteral("/1/snapshot"), outside).isEmpty());
        QVERIFY(DiffViewer::snapshotFileCandidates(stem + QStringLiteral("/1/snapshot"),
                 scratch.filePath(QStringLiteral("missing.txt"))).isEmpty());
    }
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
    void realSnapperSnapshotsAppearInRemoteBackupUi() {
#ifdef Q_OS_LINUX
        const QString configName = qEnvironmentVariable("HARBOR_GUI_QA_SNAPPER_CONFIG");
        if (configName.isEmpty())
            QSKIP("Native Btrfs/Snapper loopback fixture required");
        Btrfs btrfs;
        Snapper snapper(&btrfs, QStringLiteral("/usr/bin/snapper --no-dbus"));
        QVERIFY2(snapper.configs().contains(configName), qPrintable(configName));
        const auto expected = snapper.snapshots(configName);
        QVERIFY2(expected.size() >= 2, "two real Snapper readonly snapshots required");
        RemoteBackupWidget widget(&snapper);
        widget.show();
        QApplication::processEvents();
        QComboBox *configs = nullptr;
        for (auto *combo : widget.findChildren<QComboBox*>()) {
            if (combo->findText(configName) >= 0) {
                configs = combo;
                break;
            }
        }
        QVERIFY(configs);
        configs->setCurrentText(configName);
        QApplication::processEvents();
        QComboBox *snapshots = nullptr;
        QComboBox *parent = nullptr;
        for (auto *combo : widget.findChildren<QComboBox*>()) {
            if (combo->count() == expected.size() &&
                combo->itemData(0).toUInt() == expected.first().number)
                snapshots = combo;
            if (combo->count() == expected.size() + 1 &&
                combo->itemData(0).toUInt() == 0 &&
                combo->itemData(1).toUInt() == expected.first().number)
                parent = combo;
        }
        QVERIFY2(snapshots, "live Snapper snapshots absent from Harbor UI");
        QVERIFY2(parent, "live Snapper incremental parent selector absent");
        for (const auto &snapshot : expected) {
            QVERIFY(snapshot.number > 0);
            bool found = false;
            for (int i = 0; i < snapshots->count(); ++i)
                found |= snapshots->itemData(i).toUInt() == snapshot.number;
            QVERIFY2(found, "snapshot number missing in the GUI");
        }
        auto *refresh = button(widget, QStringLiteral("Refresh snapshots"));
        QVERIFY(refresh);
        QTest::mouseClick(refresh, Qt::LeftButton);
        QApplication::processEvents();
        QVERIFY2(snapshots->count() >= expected.size(), "refresh lost Snapper snapshots");
        // A description is user-controlled and must never be passed to a shell.
        QTemporaryDir safeScratch;
        QVERIFY(safeScratch.isValid());
        const QString marker = safeScratch.filePath(QStringLiteral("should-not-exist"));
        const QString suspect = QStringLiteral("Harbor QA ' ; touch ") + marker + QStringLiteral("; #");
        const auto result = snapper.createSnapshot(configName, suspect);
        QCOMPARE(result.exitCode, 0);
        QVERIFY2(!QFileInfo::exists(marker), "user snapshot text executed as a shell command");
        snapper.load();
        uint created = 0;
        for (const auto &snap : snapper.snapshots(configName)) {
            if (snap.desc == suspect) created = snap.number;
        }
        QVERIFY2(created > 0, "full user snapshot description not retained verbatim");
        QCOMPARE(snapper.deleteSnapshot(configName, int(created)).exitCode, 0);
        QVERIFY(!QFileInfo::exists(marker));
#endif
    }
    void keyboardFocusAndAccessibilityNamesForCriticalControls() {
        RemoteBackupWidget w(nullptr);
        w.resize(1040, 900);
        w.show();
        QApplication::processEvents();
        QAccessibleInterface *window = QAccessible::queryAccessibleInterface(&w);
        QVERIFY(window);
        QVERIFY(window->isValid());
        for (const auto &label : QStringList{
                 QStringLiteral("Cancel current operation"),
                 QStringLiteral("Send selected snapshot"),
                 QStringLiteral("Verify selected archive"),
                 QStringLiteral("List remote backups")}) {
            QPushButton *control = button(w, label);
            QVERIFY2(control, qPrintable(label));
            QAccessibleInterface *accessible = QAccessible::queryAccessibleInterface(control);
            QVERIFY2(accessible, qPrintable(label));
            QVERIFY(accessible->isValid());
            QCOMPARE(accessible->role(), QAccessible::PushButton);
            QCOMPARE(accessible->text(QAccessible::Name), label);
            // Disabled destructive actions remain discoverable to AT-SPI but
            // must not accept keyboard focus until their preconditions hold.
            QVERIFY(control->focusPolicy() != Qt::NoFocus);
            if (control->isEnabled()) {
                control->setFocus(Qt::TabFocusReason);
                QApplication::processEvents();
                QVERIFY2(control->hasFocus(), qPrintable(label));
            }
        }
        auto *engine = backend(w);
        QVERIFY(engine && engine->isEnabled());
        engine->setFocus(Qt::TabFocusReason);
        QApplication::processEvents();
        QVERIFY(engine->hasFocus());
    }
    void existingNetworkBackupDestinationPersistsAcrossSessions() {
        QSettings saved(QStringLiteral("BtrfsAssistantHarbor"), QStringLiteral("Harbor"));
        const bool previouslySet = saved.contains(QStringLiteral("remote/targetPath"));
        const QVariant previous = saved.value(QStringLiteral("remote/targetPath"));
        const QString oldRoot = QStringLiteral("/mnt/qa-existing/Workstations");
        const QString newRoot = QStringLiteral("/mnt/qa-existing/Workstations-v2");
        saved.setValue(QStringLiteral("remote/targetPath"), oldRoot);
        auto findTarget = [](RemoteBackupWidget &widget) -> QLineEdit * {
            for (auto *edit : widget.findChildren<QLineEdit*>()) {
                if (edit->placeholderText().contains(QStringLiteral("NFS/SMB")))
                    return edit;
            }
            return nullptr;
        };
        {
            RemoteBackupWidget first(nullptr);
            auto *target = findTarget(first);
            QVERIFY(target != nullptr);
            QCOMPARE(target->text(), oldRoot);
            target->setText(newRoot);
            QSettings updated(QStringLiteral("BtrfsAssistantHarbor"), QStringLiteral("Harbor"));
            QCOMPARE(updated.value(QStringLiteral("remote/targetPath")).toString(), newRoot);
        }
        {
            RemoteBackupWidget second(nullptr);
            auto *target = findTarget(second);
            QVERIFY(target != nullptr);
            QCOMPARE(target->text(), newRoot);
        }
        if (previouslySet) saved.setValue(QStringLiteral("remote/targetPath"), previous);
        else saved.remove(QStringLiteral("remote/targetPath"));
    }

    void switchingMachineRepoOrBackendClearsStaleCatalogSelections() {
        RemoteBackupWidget widget(nullptr);
        auto *engine = backend(widget);
        QVERIFY(engine);
        auto *machine = static_cast<QLineEdit *>(nullptr);
        auto *target = static_cast<QLineEdit *>(nullptr);
        for (auto *field : widget.findChildren<QLineEdit*>()) {
            if (field->toolTip().contains(QStringLiteral("Machine identity")))
                machine = field;
            if (field->placeholderText().contains(QStringLiteral("NFS/SMB")))
                target = field;
        }
        QVERIFY(machine && target);
        const auto lists = widget.findChildren<QListWidget*>();
        QCOMPARE(lists.size(), 2);
        auto *archives = lists.at(0);
        auto *sets = lists.at(1);
        engine->setCurrentIndex(1);
        target->setText(QStringLiteral("/tmp/harbor-QA-repo-A"));
        machine->setText(QStringLiteral("Pegasus"));
        archives->addItem(QStringLiteral("m@Pegasus@snap-root-42"));
        sets->addItem(QStringLiteral("legacy-machine-set"));
        QCOMPARE(archives->count(), 1);
        QCOMPARE(sets->count(), 1);
        machine->setText(QStringLiteral("Galactica"));
        QCOMPARE(archives->count(), 0);
        QCOMPARE(sets->count(), 0);
        archives->addItem(QStringLiteral("m@Galactica@snap-root-42"));
        target->setText(QStringLiteral("/tmp/harbor-QA-repo-B"));
        QCOMPARE(archives->count(), 0);
        archives->addItem(QStringLiteral("old-legacy-entry"));
        engine->setCurrentIndex(0);
        QCOMPARE(archives->count(), 0);
        QCOMPARE(sets->count(), 0);
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
                 "Cancel current operation"), QStringLiteral("Annuler l'opération en cours"));
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
    void chineseRemoteBackupUiRetainsWarningsAndActions() {
        QTranslator translator;
        const QString qm = QCoreApplication::applicationDirPath()
                           + "/btrfsassistant_zh_CN.qm";
        QVERIFY2(translator.load(qm), qPrintable(qm));
        QCoreApplication::installTranslator(&translator);
        QCOMPARE(QCoreApplication::translate("RemoteBackupWidget", "CAS machine name"),
                 QString::fromUtf8("CAS 机器名称"));
        QCOMPARE(QCoreApplication::translate("RemoteBackupWidget", "Cancel current operation"),
                 QString::fromUtf8("取消当前操作"));
        QCOMPARE(QCoreApplication::translate("RemoteBackupWidget", "Archive belongs to another machine"),
                 QString::fromUtf8("归档属于另一台机器"));
        QCOMPARE(QCoreApplication::translate("RemoteBackupWidget", "Confirm destructive CAS cleanup"),
                 QString::fromUtf8("确认破坏性 CAS 清理"));
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
    void cancellationTerminatesIsolatedProcessGroup() {
#ifdef Q_OS_UNIX
        RemoteBackupWidget w(nullptr);
        w.show();
        QApplication::processEvents();
        auto *cancel = button(w, "Cancel current operation");
        QVERIFY(cancel);
        QVERIFY(!cancel->isEnabled());
        const auto children = w.findChildren<QProcess*>();
        QCOMPARE(children.size(), 1);
        auto *process = children[0];
        process->start(QStringLiteral("/bin/sh"),
                       {QStringLiteral("-c"), QStringLiteral("sleep 45 & wait")});
        QVERIFY(process->waitForStarted(5000));
        const auto group = static_cast<pid_t>(process->processId());
        QVERIFY(group > 1);
        cancel->setEnabled(true);
        QTest::mouseClick(cancel, Qt::LeftButton);
        QTRY_COMPARE_WITH_TIMEOUT(process->state(), QProcess::NotRunning, 7000);
        QVERIFY(!cancel->isEnabled());
        // Closing only the shell would leave "sleep" behind. Reap the group.
        QTRY_VERIFY_WITH_TIMEOUT(!groupHasRunningMembers(group), 7000);
#endif
    }
    // Real FastCDC/BLAKE3 transfer, not a shell "sleep" mock. Run this
    // explicit QA gate with HARBOR_GUI_QA_TRANSPORT=<built-new-binary>.
    // It does NOT claim a real Btrfs ioctl send in this test environment.
    void cancellationDuringRealCasTransferRejectsPartialManifestAndAllowsRetry() {
#ifdef Q_OS_UNIX
        const QString binary = qEnvironmentVariable("HARBOR_GUI_QA_TRANSPORT");
        if (binary.isEmpty() || !QFileInfo(binary).isExecutable())
            QSKIP("real CAS gate requires HARBOR_GUI_QA_TRANSPORT pointing to tested binary");
        QTemporaryDir scratch;
        QVERIFY2(scratch.isValid(), qPrintable(scratch.errorString()));
        const QString repository = scratch.filePath("Workstations");
        QVERIFY(QDir().mkdir(repository));
        QCOMPARE(QProcess::execute(binary, {"init", "--repo", repository, "--allow-local"}), 0);
        const QString input = scratch.filePath("real-input.bin");
        {
            QFile source(input);
            QVERIFY(source.open(QIODevice::WriteOnly));
            QByteArray block(1024 * 1024, Qt::Uninitialized);
            QRandomGenerator rng(20261021);
            for (int i = 0; i < 384; ++i) {
                rng.fillRange(reinterpret_cast<quint32*>(block.data()), block.size() / sizeof(quint32));
                QCOMPARE(source.write(block), qint64(block.size()));
            }
            source.close();
        }
        const QString archive = "cancelled-active-cas-transfer";
        const QStringList args = {"ingest-file", "--repo", repository, "--name", archive,
                                  "--file", input, "--experimental", "--allow-local"};
        RemoteBackupWidget widget(nullptr);
        widget.show();
        QApplication::processEvents();
        auto *cancel = button(widget, "Cancel current operation");
        auto *process = widget.findChild<QProcess*>();
        QVERIFY(cancel && process);
        process->setProgram(binary);
        process->setArguments(args);
        process->start();
        QVERIFY(process->waitForStarted(5000));
        cancel->setEnabled(true);
        QElapsedTimer deadline;
        deadline.start();
        bool sawCommittedChunk = false;
        while (deadline.elapsed() < 20000 && process->state() != QProcess::NotRunning) {
            QApplication::processEvents(QEventLoop::AllEvents, 20);
            QDirIterator it(repository + "/objects", QDir::Files, QDirIterator::Subdirectories);
            if (it.hasNext()) {
                sawCommittedChunk = true;
                break;
            }
            QThread::msleep(5);
        }
        QVERIFY2(sawCommittedChunk, "transfer exited before first object; test is inconclusive");
        const pid_t group = static_cast<pid_t>(process->processId());
        QVERIFY(group > 1);
        QTest::mouseClick(cancel, Qt::LeftButton);
        QTRY_COMPARE_WITH_TIMEOUT(process->state(), QProcess::NotRunning, 10000);
        QVERIFY(!QFileInfo::exists(repository + "/manifests/" + archive + ".json"));
        QTRY_VERIFY_WITH_TIMEOUT(!groupHasRunningMembers(group), 10000);
        QCOMPARE(QProcess::execute(binary, args), 0);
        QCOMPARE(QProcess::execute(binary, {"verify", "--repo", repository, "--name", archive}), 0);
#endif
    }
    // Execute only inside a disposable Linux Btrfs guest with an actual
    // read-only snapshot and root-owned harbor-transport. This exercises the
    // real btrfs send subprocess and the actual Qt Cancel button.
    void cancellationDuringRealBtrfsSendPreservesRepository() {
#ifdef Q_OS_UNIX
        const QString binary = qEnvironmentVariable("HARBOR_GUI_QA_TRANSPORT");
        const QString snapshot = qEnvironmentVariable("HARBOR_GUI_QA_BTRFS_SNAPSHOT");
        const QString stagingRoot = qEnvironmentVariable("HARBOR_GUI_QA_BTRFS_STAGING_ROOT");
        if (binary.isEmpty() || snapshot.isEmpty() || stagingRoot.isEmpty())
            QSKIP("Btrfs guest QA requires transport, read-only snapshot and Btrfs staging root");
        QVERIFY(QFileInfo(binary).isExecutable());
        QVERIFY(QFileInfo(snapshot).isDir());
        QTemporaryDir lab(QStringLiteral("/var/tmp/harbor-qt-real-btrfs-XXXXXX"));
        QVERIFY2(lab.isValid(), qPrintable(lab.errorString()));
        const QString repo = lab.filePath("Workstations");
        QVERIFY(QDir().mkdir(repo));
        QCOMPARE(QProcess::execute(binary, {"init", "--repo", repo, "--allow-local"}), 0);
        const QString name = "real-btrfs-gui-cancel-qa";
        const QStringList sendArgs = {"send", "--repo", repo, "--name", name,
            "--snapshot", snapshot, "--experimental", "--allow-local", "--retries", "0"};
        RemoteBackupWidget widget(nullptr);
        widget.show();
        QApplication::processEvents();
        auto *process = widget.findChild<QProcess*>();
        auto *cancel = button(widget, "Cancel current operation");
        QVERIFY(process && cancel);
        process->start(binary, sendArgs);
        QVERIFY(process->waitForStarted(5000));
        cancel->setEnabled(true);
        QElapsedTimer deadline;
        deadline.start();
        bool sawChunk = false;
        while (deadline.elapsed() < 25000 && process->state() != QProcess::NotRunning) {
            QApplication::processEvents(QEventLoop::AllEvents, 20);
            QDirIterator it(repo + "/objects", QDir::Files, QDirIterator::Subdirectories);
            if (it.hasNext()) { sawChunk = true; break; }
            QThread::msleep(10);
        }
        if (!sawChunk && process->state() != QProcess::NotRunning)
            QTest::mouseClick(cancel, Qt::LeftButton);
        QVERIFY2(sawChunk, "Btrfs send finished or blocked before first immutable chunk; cancel test inconclusive");
        const pid_t group = static_cast<pid_t>(process->processId());
        QVERIFY(group > 1);
        QTest::mouseClick(cancel, Qt::LeftButton);
        QTRY_COMPARE_WITH_TIMEOUT(process->state(), QProcess::NotRunning, 12000);
        QTRY_VERIFY_WITH_TIMEOUT(!groupHasRunningMembers(group), 12000);
        QVERIFY(!QFileInfo::exists(repo + "/manifests/" + name + ".json"));
        QCOMPARE(QProcess::execute(binary, sendArgs), 0);
        QCOMPARE(QProcess::execute(binary, {"verify-stream", "--repo", repo, "--name", name}), 0);
        // btrfs receive cannot restore a native subvolume onto ext4 /var/tmp.
        // The fixture provides a separate disposable mounted Btrfs test root.
        QTemporaryDir btrfsStage(stagingRoot + QStringLiteral("/harbor-qt-stage-XXXXXX"));
        QVERIFY2(btrfsStage.isValid(), qPrintable(btrfsStage.errorString()));
        const QString staging = btrfsStage.filePath("receive");
        QVERIFY(QDir().mkdir(staging));
        QCOMPARE(QProcess::execute(binary, {"receive", "--repo", repo, "--name", name,
                   "--staging", staging, "--confirm"}), 0);
        const QString recovered = staging + "/" + QFileInfo(snapshot).fileName();
        QVERIFY2(QFileInfo(recovered).isDir(), qPrintable(recovered));
        QCOMPARE(QProcess::execute(QStringLiteral("cmp"),
            {snapshot + QStringLiteral("/payload.bin"),
             recovered + QStringLiteral("/payload.bin")}), 0);
        // Remove only the subvolume created in this test's isolated staging.
        QCOMPARE(QProcess::execute(QStringLiteral("btrfs"),
            {QStringLiteral("subvolume"), QStringLiteral("delete"), recovered}), 0);
#endif
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
