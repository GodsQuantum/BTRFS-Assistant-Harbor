#include "ui/RemoteBackupWidget.h"
#include "util/RemoteBackupPlan.h"
#include "util/MachineSetProtocol.h"
#include "util/Snapper.h"

#include <QCheckBox>
#include <QComboBox>
#include <QDateTime>
#include <QDir>
#include <QFileInfo>
#include <QFileDialog>
#include <QFormLayout>
#include <QGroupBox>
#include <QGridLayout>
#include <QHBoxLayout>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLabel>
#include <QLineEdit>
#include <QListWidget>
#include <QMessageBox>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QRegularExpression>
#include <QStandardPaths>
#include <QUuid>
#include <QVBoxLayout>

RemoteBackupWidget::RemoteBackupWidget(Snapper *snapper, QWidget *parent)
    : QWidget(parent), m_snapper(snapper), m_backend(new QComboBox(this)),
      m_parentSnapshots(new QComboBox(this)), m_configs(new QComboBox(this)),
      m_snapshots(new QComboBox(this)), m_target(new QLineEdit(this)),
      m_staging(new QLineEdit(this)), m_frequency(new QComboBox(this)), m_allowLocal(new QCheckBox(tr("Allow explicitly selected local destination"), this)),
      m_archives(new QListWidget(this)), m_machineSets(new QListWidget(this)), m_log(new QPlainTextEdit(this)),
      m_state(new QLabel(tr("Ready: no backup in progress"), this)), m_send(new QPushButton(tr("Send selected snapshot"), this)),
      m_process(new QProcess(this))
{
    auto *layout = new QVBoxLayout(this);
    auto *title = new QLabel(tr("Remote backups — Snapper snapshots"), this);
    QFont font = title->font();
    font.setPointSize(font.pointSize() + 2);
    font.setBold(true);
    title->setFont(font);
    layout->addWidget(title);
    auto *info = new QLabel(tr("Snapshots and local rollback remain managed by Snapper. "
                               "Harbor handles remote transport, verification and retrieval. "
                               "No Snapper history is recursively copied."), this);
    info->setWordWrap(true);
    layout->addWidget(info);

    auto *settings = new QGroupBox(tr("Source and destination"), this);
    auto *form = new QFormLayout(settings);
    auto *snapshotRow = new QWidget(settings);
    auto *snapshotLayout = new QHBoxLayout(snapshotRow);
    snapshotLayout->setContentsMargins(0, 0, 0, 0);
    auto *refresh = new QPushButton(tr("Refresh snapshots"), snapshotRow);
    snapshotLayout->addWidget(m_snapshots, 1);
    snapshotLayout->addWidget(refresh);
    m_backend->addItem(tr("Harbor checkpoint v2 — compatible archives"), QStringLiteral("legacy"));
    m_backend->addItem(tr("Harbor CAS / FastCDC — experimental"), QStringLiteral("cas"));
    form->addRow(tr("Backup engine"), m_backend);
    form->addRow(tr("Snapper configuration"), m_configs);
    form->addRow(tr("Readonly snapshot"), snapshotRow);
    form->addRow(tr("Incremental parent (CAS)"), m_parentSnapshots);
    m_target->setPlaceholderText(tr("Existing NFS/SMB mount or local backup directory"));
    auto *targetRow = new QWidget(settings);
    auto *targetLayout = new QHBoxLayout(targetRow);
    targetLayout->setContentsMargins(0, 0, 0, 0);
    auto *browse = new QPushButton(tr("Browse"), targetRow);
    targetLayout->addWidget(m_target, 1);
    targetLayout->addWidget(browse);
    form->addRow(tr("Destination"), targetRow);
    form->addRow(QString(), m_allowLocal);
    m_staging->setPlaceholderText(tr("Empty Btrfs staging directory for a restored snapshot"));
    form->addRow(tr("Recovery staging"), m_staging);
    m_frequency->addItem(tr("Hourly"), QStringLiteral("hourly"));
    m_frequency->addItem(tr("Daily"), QStringLiteral("daily"));
    m_frequency->addItem(tr("Weekly"), QStringLiteral("weekly"));
    form->addRow(tr("Scheduled transfer"), m_frequency);
    layout->addWidget(settings);

    auto *actions = new QGridLayout();
    auto *inventory = new QPushButton(tr("List remote backups"), this);
    auto *interrupted = new QPushButton(tr("Interrupted transfers"), this);
    auto *resume = new QPushButton(tr("Resume selected"), this);
    auto *schedule = new QPushButton(tr("Enable schedule"), this);
    auto *unschedule = new QPushButton(tr("Disable schedule"), this);
    auto *schedules = new QPushButton(tr("Scheduled backups"), this);
    auto *initCas = new QPushButton(tr("Initialize CAS destination"), this);
    auto *verify = new QPushButton(tr("Verify selected archive"), this);
    auto *prune = new QPushButton(tr("Delete selected CAS backup"), this);
    auto *sweepOrphans = new QPushButton(tr("Reclaim unused CAS chunks"), this);
    auto *recover = new QPushButton(tr("Preview recovery"), this);
    // Two rows prevent button overflow on HiDPI 13-inch laptops.
    actions->addWidget(m_send, 0, 0);
    actions->addWidget(inventory, 0, 1);
    actions->addWidget(interrupted, 0, 2);
    actions->addWidget(resume, 0, 3);
    actions->addWidget(verify, 1, 0);
    actions->addWidget(recover, 1, 1);
    actions->addWidget(schedule, 1, 2);
    actions->addWidget(initCas, 1, 3);
    actions->addWidget(schedules, 2, 0);
    actions->addWidget(unschedule, 2, 1);
    actions->addWidget(prune, 2, 2);
    actions->addWidget(sweepOrphans, 2, 3);
    layout->addLayout(actions);
    layout->addWidget(new QLabel(tr("Select a completed archive to verify/recover, or an interrupted transfer to resume"), this));
    m_archives->setMinimumHeight(100);
    layout->addWidget(m_archives);

    // Historical machine-set catalog is intentionally separated from the
    // single-archive list. Preview only: never format disks or mark bootable.
    auto *machineBox = new QGroupBox(tr("Whole-computer backup sets — checkpoint-v2 (QA)"), this);
    auto *machineLayout = new QVBoxLayout(machineBox);
    auto *machineActions = new QHBoxLayout();
    auto *auditMachine = new QPushButton(tr("Audit backup coverage"), machineBox);
    auto *listMachines = new QPushButton(tr("List machine backup sets"), machineBox);
    auto *previewMachine = new QPushButton(tr("Preview staged machine restore"), machineBox);
    machineActions->addWidget(auditMachine);
    machineActions->addWidget(listMachines);
    machineActions->addWidget(previewMachine);
    machineLayout->addLayout(machineActions);
    m_machineSets->setMinimumHeight(72);
    machineLayout->addWidget(m_machineSets);
    auto *machineNote = new QLabel(tr(
        "Historical machine sets may include separate Btrfs volumes and EFI files. "
        "The preview validates an empty Btrfs staging directory; it never restores "
        "the active system or claims the backup is bootable. "
        "CAS and checkpoint-v2 repositories have different formats."), machineBox);
    machineNote->setWordWrap(true);
    machineLayout->addWidget(machineNote);
    layout->addWidget(machineBox);
    layout->addWidget(m_state);
    m_log->setReadOnly(true);
    m_log->setMaximumBlockCount(1500);
    m_log->setPlaceholderText(tr("Transfers run asynchronously; process output appears here."));
    layout->addWidget(m_log, 1);

    if (m_snapper != nullptr) {
        m_configs->addItems(m_snapper->configs());
    }
    connect(m_configs, &QComboBox::currentTextChanged, this, [this] { refreshSnapshots(); });
    connect(m_backend, &QComboBox::currentIndexChanged, this, [this, resume, interrupted, initCas, prune, sweepOrphans] {
        const bool cas = isCasMode();
        resume->setEnabled(!cas);
        interrupted->setEnabled(!cas);
        initCas->setEnabled(cas);
        prune->setEnabled(cas);
        sweepOrphans->setEnabled(cas);
        m_parentSnapshots->setEnabled(cas);
    });
    // Initialize the UI immediately; do not leave disabled controls active.
    schedule->setEnabled(true);
    initCas->setEnabled(false);
    prune->setEnabled(false);
    sweepOrphans->setEnabled(false);
    m_parentSnapshots->setEnabled(false);
    connect(refresh, &QPushButton::clicked, this, [this] {
        if (m_snapper) m_snapper->load();
        m_configs->clear();
        if (m_snapper) m_configs->addItems(m_snapper->configs());
        refreshSnapshots();
    });
    connect(browse, &QPushButton::clicked, this, [this] {
        const QString path = QFileDialog::getExistingDirectory(this, tr("Choose a mounted backup destination"), m_target->text());
        if (!path.isEmpty()) m_target->setText(path);
    });
    connect(m_send, &QPushButton::clicked, this, [this] {
        const auto num = m_snapshots->currentData().toUInt();
        if (isCasMode()) {
            const unsigned parentNum = m_parentSnapshots->currentData().toUInt();
            const QString current = snapperSourcePath(num);
            const QString parentSnapshot = parentNum > 0 ? snapperSourcePath(parentNum) : QString();
            const auto args = HarborRemote::casSendArguments(
                m_target->text(), m_configs->currentText(), num, current,
                parentNum > 0, parentSnapshot, parentNum, m_allowLocal->isChecked());
            if (args.isEmpty() || !QFileInfo(current).isDir()) {
                QMessageBox::warning(this, tr("Invalid Btrfs source"),
                    tr("Choose an accessible Snapper snapshot path and an initialized CAS repository."));
                return;
            }
            if (QMessageBox::question(this, tr("Experimental CAS send"),
                tr("Send the selected readonly Snapper snapshot using the experimental content-addressed engine? "
                   "This creates a distinct CAS archive format; it does not overwrite previous Harbor archives.")) == QMessageBox::Yes)
                launch(args, QStringLiteral("cas-send"), QStringLiteral("harbor-transport"));
            return;
        }
        const auto name = HarborRemote::archiveName(m_configs->currentText(), num);
        const auto args = HarborRemote::sendArguments(m_configs->currentText(), num, m_target->text(), m_allowLocal->isChecked());
        if (args.isEmpty()) { QMessageBox::warning(this, tr("Invalid selection"), tr("Select a valid Snapper snapshot and an absolute destination.")); return; }
        if (QMessageBox::question(this, tr("Start backup"), tr("Send snapshot %1 to %2?").arg(name, m_target->text())) == QMessageBox::Yes)
            launch(args, QStringLiteral("send"));
    });
    connect(initCas, &QPushButton::clicked, this, [this] {
        const auto args = HarborRemote::casInitArguments(m_target->text(), m_allowLocal->isChecked());
        if (args.isEmpty()) {
            QMessageBox::warning(this, tr("Invalid destination"), tr("Select an existing absolute CAS directory."));
            return;
        }
        if (QMessageBox::question(this, tr("Initialize CAS"),
            tr("Initialize or open the dedicated CAS repository in this destination? "
               "Existing legacy archives are not modified.")) == QMessageBox::Yes)
            launch(args, QStringLiteral("cas-init"), QStringLiteral("harbor-transport"));
    });
    connect(auditMachine, &QPushButton::clicked, this, [this] {
        launch(HarborRemote::machineInventoryArguments(), QStringLiteral("machine-inventory"));
    });
    connect(listMachines, &QPushButton::clicked, this, [this] {
        const auto args = HarborRemote::machineSetListArguments(m_target->text());
        if (args.isEmpty()) {
            QMessageBox::warning(this, tr("Invalid legacy repository"),
                tr("Select an absolute checkpoint-v2 repository before listing machine sets."));
            return;
        }
        m_machineListRepo = m_target->text();
        launch(args, QStringLiteral("machine-set-list"));
    });
    connect(previewMachine, &QPushButton::clicked, this, [this] {
        const auto *selected = m_machineSets->currentItem();
        const QString id = selected == nullptr ? QString() : selected->data(Qt::UserRole).toString();
        if (selected != nullptr &&
            selected->data(Qt::UserRole + 1).toString() != m_target->text()) {
            QMessageBox::warning(this, tr("Machine repository changed"),
                tr("The destination changed since listing machine sets. Refresh the catalog first."));
            return;
        }
        const auto args = HarborRemote::machineSetPreviewArguments(
            m_target->text(), id, m_staging->text());
        if (args.isEmpty()) {
            QMessageBox::warning(this, tr("Invalid machine restore preview"),
                tr("Select an existing machine backup set and a new empty Btrfs staging directory. "
                   "This operation never changes the running system."));
            return;
        }
        m_machinePreviewRepo = m_target->text();
        m_machinePreviewStaging = m_staging->text();
        m_machinePreviewId = id;
        launch(args, QStringLiteral("machine-set-preview"));
    });
    connect(inventory, &QPushButton::clicked, this, &RemoteBackupWidget::listArchives);
    connect(interrupted, &QPushButton::clicked, this, &RemoteBackupWidget::listTransfers);
    connect(resume, &QPushButton::clicked, this, [this] {
        const auto *item = m_archives->currentItem();
        const QString transferId = item != nullptr ? item->data(Qt::UserRole + 1).toString() : QString();
        const QString archive = selectedArchive();
        const auto arguments = HarborRemote::resumeArguments(
            m_target->text(), archive, transferId, m_allowLocal->isChecked());
        if (arguments.isEmpty()) {
            QMessageBox::warning(this, tr("No resumable transfer"),
                tr("Open Interrupted transfers, then select a valid partial checkpoint."));
            return;
        }
        if (QMessageBox::question(this, tr("Resume checkpoint"),
            tr("Resume archive %1 using its existing verified checkpoints? "
               "An active transfer holds a lock and cannot be opened twice.").arg(archive)) == QMessageBox::Yes)
            launch(arguments, QStringLiteral("resume"));
    });
    connect(schedule, &QPushButton::clicked, this, [this] {
        const QStringList args = HarborRemote::scheduleInstallerArguments(
            m_configs->currentText(), m_target->text(), m_frequency->currentData().toString(),
            m_allowLocal->isChecked(), isCasMode());
        if (args.isEmpty()) {
            QMessageBox::warning(this, tr("Invalid schedule"), tr("Choose a valid Snapper config, destination and frequency."));
            return;
        }
        if (QMessageBox::question(this, tr("Install systemd timer"),
                tr("Install and enable an automatic %1 transfer for %2? It will use the selected engine. Snapper snapshots will not be created or deleted.")
                    .arg(m_frequency->currentText(), m_configs->currentText())) != QMessageBox::Yes) return;
        launch(args, QStringLiteral("schedule"), QStringLiteral("btrfs-assistant-harbor-schedule"));
    });
    connect(schedules, &QPushButton::clicked, this, [this] {
        launch({QStringLiteral("list")}, QStringLiteral("list-schedules"),
               QStringLiteral("btrfs-assistant-harbor-schedule"));
    });
    connect(unschedule, &QPushButton::clicked, this, [this] {
        const QString id = HarborRemote::profileIdForEngine(
            m_configs->currentText(), m_target->text(), isCasMode());
        if (id.isEmpty()) {
            QMessageBox::warning(this, tr("Invalid schedule"), tr("Choose an existing Snapper configuration and destination."));
            return;
        }
        if (QMessageBox::question(this, tr("Disable schedule"),
                tr("Stop and remove the automatic timer for this configuration and destination? No snapshot or backup files will be deleted.")) != QMessageBox::Yes)
            return;
        launch({QStringLiteral("remove"), QStringLiteral("--profile-id"), id},
               QStringLiteral("unschedule"), QStringLiteral("btrfs-assistant-harbor-schedule"));
    });
    connect(prune, &QPushButton::clicked, this, [this] {
        const QString archive = selectedArchive();
        const QStringList args = HarborRemote::casPrunePreviewArguments(m_target->text(), archive);
        if (!isCasMode() || archive.isEmpty() || args.isEmpty()) {
            QMessageBox::warning(this, tr("No CAS archive selected"), tr("Select a committed CAS archive."));
            return;
        }
        m_pendingPruneRepo = m_target->text();
        m_pendingPruneArchive = archive;
        launch(args, QStringLiteral("cas-prune-preview"), QStringLiteral("harbor-transport"));
    });
    connect(sweepOrphans, &QPushButton::clicked, this, [this] {
        const QStringList args = HarborRemote::casPrunePreviewArguments(m_target->text());
        if (!isCasMode() || args.isEmpty()) {
            QMessageBox::warning(this, tr("Invalid CAS destination"), tr("Choose a CAS repository first."));
            return;
        }
        m_pendingPruneRepo = m_target->text();
        m_pendingPruneArchive.clear();
        launch(args, QStringLiteral("cas-prune-preview"), QStringLiteral("harbor-transport"));
    });
    connect(verify, &QPushButton::clicked, this, [this] {
        if (isCasMode()) {
            const auto args = HarborRemote::casVerifyArguments(m_target->text(), selectedArchive());
            if (args.isEmpty()) {
                QMessageBox::warning(this, tr("Missing archive"), tr("Select a completed CAS archive."));
                return;
            }
            launch(args, QStringLiteral("cas-verify"), QStringLiteral("harbor-transport"));
            return;
        }
        const auto args = HarborRemote::verifyArguments(m_target->text(), selectedArchive());
        if (args.isEmpty()) { QMessageBox::warning(this, tr("Missing archive"), tr("Select a valid archive and destination.")); return; }
        launch(args, QStringLiteral("verify"));
    });
    connect(recover, &QPushButton::clicked, this, [this] {
        if (isCasMode()) {
            m_pendingRestore = HarborRemote::casPreviewArguments(m_target->text(), selectedArchive(), m_staging->text());
            if (m_pendingRestore.isEmpty()) {
                QMessageBox::warning(this, tr("Invalid recovery"), tr("Choose an archive and an empty absolute Btrfs staging directory."));
                return;
            }
            launch(m_pendingRestore, QStringLiteral("restore-preview-cas"), QStringLiteral("harbor-transport"));
            return;
        }
        m_pendingRestore = HarborRemote::previewRestoreArguments(m_target->text(), selectedArchive(), m_staging->text());
        if (m_pendingRestore.isEmpty()) { QMessageBox::warning(this, tr("Invalid recovery"), tr("Select an archive and an absolute non-root staging directory.")); return; }
        launch(m_pendingRestore, QStringLiteral("restore-preview"));
    });
    connect(m_process, &QProcess::readyReadStandardOutput, this, [this] {
        const QByteArray data = m_process->readAllStandardOutput();
        if (m_stdout.size() < 2 * 1024 * 1024) m_stdout.append(data.left(2 * 1024 * 1024 - m_stdout.size()));
        appendOutput(QString::fromUtf8(data));
    });
    connect(m_process, &QProcess::readyReadStandardError, this, [this] {
        m_stderrBuffer.append(m_process->readAllStandardError());
        if (m_stderrBuffer.size() > 65536) {
            appendOutput(tr("Backend diagnostic line exceeded 64 KiB; truncating."));
            m_stderrBuffer.clear();
            return;
        }
        static const QRegularExpression bytesPattern(QStringLiteral("^HARBOR_PROGRESS_BYTES=([0-9]+)$"));
        while (true) {
            const qsizetype newline = m_stderrBuffer.indexOf('\n');
            if (newline < 0) break;
            const QString line = QString::fromUtf8(m_stderrBuffer.left(newline)).trimmed();
            m_stderrBuffer.remove(0, newline + 1);
            const auto match = bytesPattern.match(line);
            if (match.hasMatch()) {
                bool parsed = false;
                const qulonglong bytes = match.captured(1).toULongLong(&parsed);
                if (parsed && m_transferTimer.isValid()) {
                    const qint64 ms = qMax<qint64>(m_transferTimer.elapsed(), 1);
                    const double gib = double(bytes) / (1024.0 * 1024.0 * 1024.0);
                    const double mibps = (double(bytes) / (1024.0 * 1024.0)) / (double(ms) / 1000.0);
                    m_state->setText(tr("Source stream read: %1 GiB — average %2 MiB/s (raw; total unknown)")
                                         .arg(gib, 0, 'f', 2).arg(mibps, 0, 'f', 1));
                }
            } else if (!line.isEmpty()) {
                appendOutput(line);
            }
        }
    });
    connect(m_process, &QProcess::finished, this, &RemoteBackupWidget::actionFinished);
    connect(m_process, &QProcess::errorOccurred, this, [this](QProcess::ProcessError err) {
        if (err == QProcess::FailedToStart) {
            appendOutput(tr("Harbor CLI not found or failed to start: %1").arg(m_process->errorString()));
            m_state->setText(tr("Cannot start Harbor CLI"));
            m_send->setEnabled(true);
        }
    });
    refreshSnapshots();
}

bool RemoteBackupWidget::isCasMode() const
{
    return m_backend->currentData().toString() == QLatin1String("cas");
}

QString RemoteBackupWidget::snapperSourcePath(unsigned number) const
{
    if (m_snapper == nullptr || number == 0 || m_configs->currentText().isEmpty()) return {};
    const QString subvolume = m_snapper->config(m_configs->currentText()).subvolume();
    if (!QDir::isAbsolutePath(subvolume)) return {};
    return QDir::cleanPath(subvolume + QLatin1String("/.snapshots/") +
                           QString::number(number) + QLatin1String("/snapshot"));
}

void RemoteBackupWidget::refreshSnapshots()
{
    m_snapshots->clear();
    m_parentSnapshots->clear();
    m_parentSnapshots->addItem(tr("None — full send"), 0);
    if (m_snapper == nullptr) return;
    const auto snapshots = m_snapper->snapshots(m_configs->currentText());
    for (const auto &snapshot : snapshots) {
        if (snapshot.number == 0) continue;
        const QString label = QStringLiteral("#%1 — %2 — %3")
                                  .arg(snapshot.number)
                                  .arg(snapshot.time.toString(Qt::ISODate), snapshot.desc);
        m_snapshots->addItem(label, snapshot.number);
        m_parentSnapshots->addItem(label, snapshot.number);
    }
    if (m_snapshots->count()) m_snapshots->setCurrentIndex(m_snapshots->count() - 1);
}

void RemoteBackupWidget::appendOutput(const QString &output)
{
    QString display = output;
    if (display.size() > 3000) display = display.right(3000);
    m_log->appendPlainText(display.trimmed());
}

void RemoteBackupWidget::launch(const QStringList &arguments, const QString &purpose, const QString &executable)
{
    if (m_process->state() != QProcess::NotRunning) {
        QMessageBox::information(this, tr("Busy"), tr("An operation is already running."));
        return;
    }
    const QString cli = QStandardPaths::findExecutable(executable);
    if (cli.isEmpty() || !HarborRemote::trustedBackendExecutable(cli)) {
        QMessageBox::critical(this, tr("Backend not trusted"),
            tr("The backup backend must be installed as a root-owned executable in /usr/bin or "
               "/usr/local/bin, with no group/world-write permission, and with trusted parent directories. "
               "Refusing to run an executable from the user PATH: %1").arg(executable));
        return;
    }
    m_purpose = purpose;
    m_stdout.clear();
    m_stderrBuffer.clear();
    m_transferTimer.start();
    m_send->setEnabled(false);
    m_state->setText(tr("Running: %1").arg(purpose));
    m_process->setProgram(cli);
    m_process->setArguments(arguments);
    m_process->start();
}

void RemoteBackupWidget::listArchives()
{
    if (isCasMode()) {
        const auto args = HarborRemote::casListArguments(m_target->text());
        if (args.isEmpty()) {
            QMessageBox::warning(this, tr("Invalid destination"), tr("Choose an absolute CAS directory."));
            return;
        }
        launch(args, QStringLiteral("list"), QStringLiteral("harbor-transport"));
        return;
    }
    const auto args = HarborRemote::listArguments(m_target->text());
    if (args.isEmpty()) {
        QMessageBox::warning(this, tr("Invalid destination"), tr("Choose an absolute backup directory."));
        return;
    }
    launch(args, QStringLiteral("list"));
}

void RemoteBackupWidget::listTransfers()
{
    const auto arguments = HarborRemote::transfersArguments(m_target->text());
    if (arguments.isEmpty()) {
        QMessageBox::warning(this, tr("Invalid destination"), tr("Choose an absolute backup directory."));
        return;
    }
    launch(arguments, QStringLiteral("list-transfers"));
}

QString RemoteBackupWidget::selectedArchive() const
{
    const auto *item = m_archives->currentItem();
    return item != nullptr ? item->data(Qt::UserRole).toString() : QString();
}

void RemoteBackupWidget::actionFinished(int code, QProcess::ExitStatus status)
{
    m_send->setEnabled(true);
    const bool ok = status == QProcess::NormalExit && code == 0;
    m_state->setText(ok ? tr("Operation finished: %1").arg(m_purpose)
                        : tr("Operation failed: %1 (exit %2)").arg(m_purpose).arg(code));
    if (!ok) return;
    if (m_purpose == QLatin1String("machine-inventory")) {
        QJsonParseError error{};
        const auto doc = QJsonDocument::fromJson(m_stdout, &error);
        if (error.error != QJsonParseError::NoError || !doc.isObject()) {
            appendOutput(tr("Invalid filesystem inventory response."));
            return;
        }
        const auto obj = doc.object();
        const int count = obj.value(QStringLiteral("included_btrfs_count")).toInt(-1);
        const auto warnings = obj.value(QStringLiteral("warnings")).toArray();
        const bool complete = obj.value(QStringLiteral("inventory_complete")).toBool(false);
        if (obj.value(QStringLiteral("schema_version")).toInt() != 1 ||
            count < 0 || count > 1024 || warnings.size() > 1024) {
            appendOutput(tr("Unsupported machine inventory schema or invalid counts."));
            return;
        }
        QStringList details;
        for (const auto &message : warnings) {
            if (!message.isString()) {
                appendOutput(tr("Invalid machine inventory warning; refusing result."));
                return;
            }
            if (details.size() < 8) details << message.toString().left(240);
        }
        const QString summary = tr("Detected %1 included Btrfs volumes.\nCoverage inventory: %2.\n"
                                   "Bootable bare-metal recovery: NOT CERTIFIED.\n%3")
            .arg(count).arg(complete ? tr("complete for supported mount types")
                                     : tr("incomplete — backup must be refused"))
            .arg(details.join(QStringLiteral("\n")));
        if (complete) QMessageBox::information(this, tr("Machine coverage audit"), summary);
        else QMessageBox::warning(this, tr("Missing machine coverage"), summary);
        return;
    }
    if (m_purpose == QLatin1String("machine-set-list")) {
        if (m_machineListRepo != m_target->text()) {
            appendOutput(tr("Machine-set catalog destination changed while reading; refusing stale catalog."));
            return;
        }
        QList<HarborMachineProtocol::BackupSet> list;
        QString error;
        if (!HarborMachineProtocol::catalog(m_stdout, &list, &error)) {
            appendOutput(tr("Machine-set catalog rejected: %1").arg(error));
            return;
        }
        m_machineSets->clear();
        for (const auto &record : list) {
            auto *item = new QListWidgetItem(
                tr("%1 — %2 Btrfs volumes, %3 boot-file sets — QA; NOT bootable")
                    .arg(record.id).arg(record.volumes).arg(record.bootFiles), m_machineSets);
            item->setData(Qt::UserRole, record.id);
            item->setData(Qt::UserRole + 1, m_machineListRepo);
        }
        return;
    }
    if (m_purpose == QLatin1String("machine-set-preview")) {
        if (m_machinePreviewRepo != m_target->text() ||
            m_machinePreviewStaging != m_staging->text() ||
            m_machinePreviewId.isEmpty()) {
            appendOutput(tr("Machine-set preview destination, staging or selection changed; refusing stale result."));
            return;
        }
        HarborMachineProtocol::RestorePreview plan;
        QString error;
        if (!HarborMachineProtocol::preview(m_stdout, m_machinePreviewStaging, &plan, &error)) {
            appendOutput(tr("Machine restore preview rejected: %1").arg(error));
            return;
        }
        QMessageBox::information(this, tr("Validated staged recovery preview"),
            tr("Backend preflight validated: %1 separate Btrfs volumes, %2 boot-file archives.\n"
               "Original mount points (first 12): %3\n"
               "Nothing was restored. A bootable computer is NOT promised. "
               "Bare-metal recovery still requires validated ReaR/EFI rescue.")
                .arg(plan.volumesCount).arg(plan.bootFiles).arg(plan.mounts.join(QStringLiteral(", "))));
        return;
    }
    if (m_purpose == QLatin1String("cas-prune-preview")) {
        QJsonParseError error{};
        const auto doc = QJsonDocument::fromJson(m_stdout, &error);
        if (error.error != QJsonParseError::NoError || !doc.isObject()) {
            appendOutput(tr("Prune preview invalid; refusing deletion."));
            return;
        }
        const auto obj = doc.object();
        const auto plan = obj.value(QStringLiteral("plan")).toObject();
        const QString token = plan.value(QStringLiteral("plan_sha256")).toString();
        const auto selected = plan.value(QStringLiteral("remove_archives")).toArray();
        const QStringList args = HarborRemote::casPruneConfirmArguments(
            m_pendingPruneRepo, m_pendingPruneArchive, token);
        if (obj.value(QStringLiteral("status")).toString() != QLatin1String("dry-run") ||
            args.isEmpty() || selected.size() != (m_pendingPruneArchive.isEmpty() ? 0 : 1) ||
            (!m_pendingPruneArchive.isEmpty() && selected.first().toString() != m_pendingPruneArchive) ||
            m_target->text() != m_pendingPruneRepo || !isCasMode()) {
            appendOutput(tr("Prune plan mismatch or destination changed; refusing deletion."));
            return;
        }
        const double freedMiB = plan.value(QStringLiteral("reclaim_bytes")).toDouble() / (1024.0 * 1024.0);
        const QString detail = !m_pendingPruneArchive.isEmpty()
            ? tr("Permanently delete the selected CAS archive %1 and reclaim unreferenced chunks?")
                 .arg(m_pendingPruneArchive)
            : tr("Reclaim orphan CAS chunks from aborted transfers? No committed archive will be removed.");
        if (QMessageBox::warning(this, tr("Confirm destructive CAS cleanup"),
                detail + tr("\nEstimated reclaimable compressed data: %1 MiB.\n"
                            "This cannot be undone. The plan will be checked again under repository lock.")
                             .arg(freedMiB, 0, 'f', 2),
                QMessageBox::Yes | QMessageBox::No, QMessageBox::No) == QMessageBox::Yes) {
            launch(args, QStringLiteral("cas-prune-confirm"), QStringLiteral("harbor-transport"));
        }
        return;
    }
    if (m_purpose == QLatin1String("cas-prune-confirm")) {
        appendOutput(tr("CAS pruning finished; refreshing archive inventory."));
        listArchives();
        return;
    }
    if (m_purpose == QLatin1String("list")) {
        QJsonParseError error{};
        const auto doc = QJsonDocument::fromJson(m_stdout, &error);
        if (error.error != QJsonParseError::NoError || !doc.isArray()) {
            appendOutput(tr("Archive inventory is not valid JSON; no selection was changed."));
            return;
        }
        m_archives->clear();
        for (const auto &v : doc.array()) {
            if (!v.isObject()) continue;
            const auto obj = v.toObject();
            const QString name = obj.value(QStringLiteral("name")).toString();
            if (name.isEmpty()) continue;
            auto *item = new QListWidgetItem(name, m_archives);
            item->setData(Qt::UserRole, name);
        }
    }
    if (m_purpose == QLatin1String("list-transfers")) {
        QJsonParseError error{};
        const auto doc = QJsonDocument::fromJson(m_stdout, &error);
        if (error.error != QJsonParseError::NoError || !doc.isArray()) {
            appendOutput(tr("Checkpoint inventory is invalid; no selection was changed."));
            return;
        }
        m_archives->clear();
        for (const auto &value : doc.array()) {
            if (!value.isObject()) continue;
            const auto object = value.toObject();
            const QString name = object.value(QStringLiteral("name")).toString();
            const QString transferId = object.value(QStringLiteral("transfer_id")).toString();
            const QString state = object.value(QStringLiteral("state")).toString();
            const QStringList resumable = {QStringLiteral("preparing"), QStringLiteral("uploading"),
                QStringLiteral("pause_requested"), QStringLiteral("paused"),
                QStringLiteral("replaying"), QStringLiteral("failed_resumable"), QStringLiteral("finalizing")};
            if (name.isEmpty() || !resumable.contains(state)) continue;
            if (HarborRemote::resumeArguments(m_target->text(), name, transferId, m_allowLocal->isChecked()).isEmpty())
                continue;
            auto *item = new QListWidgetItem(name + QStringLiteral(" — ") + state, m_archives);
            item->setData(Qt::UserRole, name);
            item->setData(Qt::UserRole + 1, transferId);
            item->setData(Qt::UserRole + 2, state);
        }
    }
    if (m_purpose == QLatin1String("restore-preview-cas")) {
        if (QMessageBox::question(this, tr("Confirm staged Btrfs receive"),
              tr("CAS archive chain verified. Receive every required snapshot into the selected empty Btrfs staging directory? "
                 "This will not activate a system rollback.")) == QMessageBox::Yes) {
            QStringList apply = m_pendingRestore;
            const qsizetype position = apply.indexOf(QStringLiteral("--preview"));
            if (position >= 0) apply[position] = QStringLiteral("--confirm");
            launch(apply, QStringLiteral("cas-receive"), QStringLiteral("harbor-transport"));
        }
        return;
    }
    if (m_purpose == QLatin1String("restore-preview")) {
        if (QMessageBox::question(this, tr("Confirm recovery"),
                tr("Dry-run successful. Restore the selected snapshot into the staging directory? "
                   "Existing system subvolumes will not be replaced.")) == QMessageBox::Yes) {
            QStringList apply = m_pendingRestore;
            apply.removeAll(QStringLiteral("--dry-run"));
            launch(apply, QStringLiteral("restore"));
        }
    }
}
