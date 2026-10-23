#include "ui/RemoteBackupWidget.h"
#include "util/RemoteBackupPlan.h"
#include "util/MachineSetProtocol.h"
#include "util/Snapper.h"
#include "util/HarborProgress.h"
#include "util/RecoveryStaging.h"
#include <QProgressBar>

#include <QCheckBox>
#include <QComboBox>
#include <QDateTime>
#include <QDialog>
#include <QDialogButtonBox>
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
#include <QSettings>
#include <QSysInfo>
#include <QUuid>
#include <QTimer>
#include <QTimeEdit>
#ifdef Q_OS_UNIX
#include <signal.h>
#include <unistd.h>
#endif
#include <QVBoxLayout>

RemoteBackupWidget::RemoteBackupWidget(Snapper *snapper, QWidget *parent)
    : QWidget(parent), m_snapper(snapper), m_backend(new QComboBox(this)),
      m_parentSnapshots(new QComboBox(this)), m_configs(new QComboBox(this)),
      m_snapshots(new QComboBox(this)), m_target(new QLineEdit(this)),
      m_machineName(new QLineEdit(this)),
      m_staging(new QLineEdit(this)), m_frequency(new QComboBox(this)),
      m_scheduleAt(new QTimeEdit(this)),
      m_catchUp(new QCheckBox(tr("Catch up missed backups after startup"), this)),
      m_independentSend(new QCheckBox(tr("Continue backup after closing Harbor (systemd)"), this)),
      m_allowLocal(new QCheckBox(tr("Allow explicitly selected local destination"), this)),
      m_archives(new QListWidget(this)), m_machineSets(new QListWidget(this)), m_log(new QPlainTextEdit(this)),
      m_state(new QLabel(tr("Ready: no backup in progress"), this)),
      m_progressDetails(new QLabel(this)), m_progressBar(new QProgressBar(this)), m_send(new QPushButton(tr("Send selected snapshot"), this)),
      m_cancel(new QPushButton(tr("Cancel current operation"), this)),
      m_process(new QProcess(this)), m_jobPoller(new QProcess(this))
{
    m_process->setObjectName(QStringLiteral("harborCommandProcess"));
    m_jobPoller->setObjectName(QStringLiteral("harborStatusPoller"));
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

    // The primary experience must not require choosing engines, Snapper
    // configs, volume IDs, parent snapshots, or CLI flags.
    auto *simpleActions = new QGroupBox(tr("Computer protection"), this);
    auto *simpleLayout = new QVBoxLayout(simpleActions);
    auto *wholeBackup = new QPushButton(tr("Back up the entire computer"), simpleActions);
    wholeBackup->setObjectName(QStringLiteral("harborBackupWholeComputer"));
    wholeBackup->setMinimumHeight(48);
    auto *wholeRestore = new QPushButton(tr("Restore a computer"), simpleActions);
    wholeRestore->setObjectName(QStringLiteral("harborRestoreWholeComputer"));
    wholeRestore->setMinimumHeight(48);
    simpleLayout->addWidget(wholeBackup);
    simpleLayout->addWidget(wholeRestore);
    layout->addWidget(simpleActions);

    auto *advancedToggle = new QPushButton(tr("Advanced backup options"), this);
    advancedToggle->setCheckable(true);
    advancedToggle->setChecked(false);
    advancedToggle->setObjectName(QStringLiteral("harborAdvancedOptions"));
    layout->addWidget(advancedToggle);

    auto *settings = new QGroupBox(tr("Source and destination"), this);
    auto *form = new QFormLayout(settings);
    auto *snapshotRow = new QWidget(settings);
    auto *snapshotLayout = new QHBoxLayout(snapshotRow);
    snapshotLayout->setContentsMargins(0, 0, 0, 0);
    auto *refresh = new QPushButton(tr("Refresh snapshots"), snapshotRow);
    snapshotLayout->addWidget(m_snapshots, 1);
    snapshotLayout->addWidget(refresh);
    m_backend->addItem(tr("Harbor checkpoint v2 — compatible archives"), QStringLiteral("legacy"));
    m_backend->addItem(tr("Harbor CAS — deduplicated backups"), QStringLiteral("cas"));
    form->addRow(tr("Backup engine"), m_backend);
    QString detected = QSysInfo::machineHostName();
    detected.replace(QRegularExpression(QStringLiteral("[^A-Za-z0-9_.-]")), QStringLiteral("-"));
    if (detected.isEmpty()) detected = QStringLiteral("Machine");
    QSettings harborSettings(QStringLiteral("BtrfsAssistantHarbor"), QStringLiteral("Harbor"));
    const auto preferredEngine = harborSettings.value(QStringLiteral("remote/engine"), QStringLiteral("legacy")).toString();
    const int engineIndex = m_backend->findData(preferredEngine);
    if (engineIndex >= 0) m_backend->setCurrentIndex(engineIndex);
    connect(m_backend, &QComboBox::currentIndexChanged, this, [this] {
        QSettings preferences(QStringLiteral("BtrfsAssistantHarbor"), QStringLiteral("Harbor"));
        preferences.setValue(QStringLiteral("remote/engine"), m_backend->currentData());
    });
    m_machineName->setText(harborSettings.value(QStringLiteral("cas/machineName"), detected).toString());
    m_machineName->setToolTip(tr("Machine identity inside a shared CAS repository (not a sub-repository)."));
    form->addRow(tr("CAS machine name"), m_machineName);
    connect(m_machineName, &QLineEdit::editingFinished, this, [this] {
        QSettings settings(QStringLiteral("BtrfsAssistantHarbor"), QStringLiteral("Harbor"));
        settings.setValue(QStringLiteral("cas/machineName"), m_machineName->text());
    });
    form->addRow(tr("Snapper configuration"), m_configs);
    form->addRow(tr("Readonly snapshot"), snapshotRow);
    form->addRow(tr("Incremental parent (CAS)"), m_parentSnapshots);
    m_target->setPlaceholderText(tr("Existing NFS/SMB mount or local backup directory"));
    // Reuse the user's existing repository across sessions. This only remembers
    // a path; it never creates a directory or bypasses mounted-network checks.
    const QString savedTarget = harborSettings.value(QStringLiteral("remote/targetPath"), QString()).toString();
    const QString existingPegasusRepo = QStringLiteral("/mnt/Cloud9/backup-local/Workstations");
    m_target->setText(!savedTarget.isEmpty() ? QDir::cleanPath(savedTarget)
        : QFileInfo::exists(existingPegasusRepo) ? existingPegasusRepo : QString());
    connect(m_target, &QLineEdit::editingFinished, this, [this] {
        const QString path = m_target->text();
        if (path.startsWith(QLatin1Char('/')))
            m_target->setText(QDir::cleanPath(path));
    });
    connect(m_target, &QLineEdit::textChanged, this, [this] {
        QSettings settings(QStringLiteral("BtrfsAssistantHarbor"), QStringLiteral("Harbor"));
        settings.setValue(QStringLiteral("remote/targetPath"), m_target->text());
    });
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
    m_scheduleAt->setDisplayFormat(QStringLiteral("HH:mm"));
    m_scheduleAt->setTime(QTime::fromString(harborSettings.value(
        QStringLiteral("remote/calendarAt"), QStringLiteral("03:00")).toString(),
        QStringLiteral("HH:mm")));
    form->addRow(tr("Scheduled time"), m_scheduleAt);
    auto *daysRow = new QWidget(settings);
    auto *daysLayout = new QHBoxLayout(daysRow);
    daysLayout->setContentsMargins(0, 0, 0, 0);
    const QStringList days{"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"};
    const QStringList dayLabels{tr("Mon"), tr("Tue"), tr("Wed"), tr("Thu"),
                                tr("Fri"), tr("Sat"), tr("Sun")};
    const QStringList chosen = harborSettings.value(
        QStringLiteral("remote/calendarDays"), QStringLiteral("Mon")).toString().split(
            QLatin1Char(','), Qt::SkipEmptyParts);
    for (int i = 0; i < 7; ++i) {
        m_weekdays[i] = new QCheckBox(dayLabels.at(i), daysRow);
        m_weekdays[i]->setChecked(chosen.contains(days.at(i)));
        daysLayout->addWidget(m_weekdays[i]);
        connect(m_weekdays[i], &QCheckBox::toggled, this, [this, days] {
            QStringList names;
            for (int j = 0; j < 7; ++j) if (m_weekdays[j]->isChecked()) names << days.at(j);
            QSettings p(QStringLiteral("BtrfsAssistantHarbor"), QStringLiteral("Harbor"));
            p.setValue(QStringLiteral("remote/calendarDays"), names.join(QLatin1Char(',')));
        });
    }
    form->addRow(tr("Weekly days"), daysRow);
    m_catchUp->setChecked(harborSettings.value(QStringLiteral("remote/catchUp"), true).toBool());
    form->addRow(QString(), m_catchUp);
    m_independentSend->setChecked(harborSettings.value(
        QStringLiteral("remote/independentSend"), true).toBool());
    form->addRow(QString(), m_independentSend);
    const int savedIndex = m_frequency->findData(harborSettings.value(
        QStringLiteral("remote/frequency"), QStringLiteral("daily")));
    m_frequency->setCurrentIndex(savedIndex >= 0 ? savedIndex : 1);
    const auto syncDays = [this] {
        const bool weekly = m_frequency->currentData().toString() == QLatin1String("weekly");
        for (auto *day : m_weekdays) day->setEnabled(weekly);
        QSettings p(QStringLiteral("BtrfsAssistantHarbor"), QStringLiteral("Harbor"));
        p.setValue(QStringLiteral("remote/frequency"), m_frequency->currentData());
    };
    connect(m_frequency, &QComboBox::currentIndexChanged, this, syncDays);
    syncDays();
    connect(m_scheduleAt, &QTimeEdit::timeChanged, this, [this] {
        QSettings p(QStringLiteral("BtrfsAssistantHarbor"), QStringLiteral("Harbor"));
        p.setValue(QStringLiteral("remote/calendarAt"), m_scheduleAt->time().toString(QStringLiteral("HH:mm")));
    });
    connect(m_catchUp, &QCheckBox::toggled, this, [](bool on) {
        QSettings p(QStringLiteral("BtrfsAssistantHarbor"), QStringLiteral("Harbor"));
        p.setValue(QStringLiteral("remote/catchUp"), on);
    });
    connect(m_independentSend, &QCheckBox::toggled, this, [](bool on) {
        QSettings p(QStringLiteral("BtrfsAssistantHarbor"), QStringLiteral("Harbor"));
        p.setValue(QStringLiteral("remote/independentSend"), on);
    });
    layout->addWidget(settings);

    auto *actions = new QGridLayout();
    auto *inventory = new QPushButton(tr("List remote backups"), this);
    auto *interrupted = new QPushButton(tr("Interrupted transfers"), this);
    auto *resume = new QPushButton(tr("Resume selected"), this);
    auto *schedule = new QPushButton(tr("Enable schedule"), this);
    auto *unschedule = new QPushButton(tr("Disable schedule"), this);
    auto *schedules = new QPushButton(tr("Scheduled backups"), this);
    auto *jobJournal = new QPushButton(tr("Backup journal"), this);
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
    actions->addWidget(m_cancel, 3, 0, 1, 2);
    actions->addWidget(jobJournal, 3, 2, 1, 2);
    m_cancel->setEnabled(false);
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
    settings->setVisible(false);
    machineBox->setVisible(false);
    connect(advancedToggle, &QPushButton::toggled, this,
            [settings, machineBox, actions](bool show) {
                settings->setVisible(show);
                machineBox->setVisible(show);
                // Legacy single-snapshot buttons and the separate transfer
                // catalog should stay out of the ordinary user journey.
                for (int i = 0; i < actions->count(); ++i) {
                    if (auto *item = actions->itemAt(i)) {
                        if (auto *widget = item->widget()) widget->setVisible(show);
                    }
                }
            });
    for (int i = 0; i < actions->count(); ++i) {
        if (auto *item = actions->itemAt(i)) {
            if (auto *widget = item->widget()) widget->setVisible(false);
        }
    }
    layout->addWidget(m_state);
    m_progressBar->setObjectName(QStringLiteral("harborBackupEstimatedProgress"));
    m_progressBar->setRange(0, 0);
    m_progressBar->setVisible(false);
    layout->addWidget(m_progressBar);
    m_progressDetails->setObjectName(QStringLiteral("harborBackupEstimatedETA"));
    m_progressDetails->setWordWrap(true);
    m_progressDetails->setTextFormat(Qt::PlainText);
    m_progressDetails->setVisible(false);
    layout->addWidget(m_progressDetails);
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
        m_parentSnapshots->setEnabled(cas && !m_independentSend->isChecked());
    });
    connect(m_independentSend, &QCheckBox::toggled, this, [this] {
        m_parentSnapshots->setEnabled(isCasMode() && !m_independentSend->isChecked());
    });
    // Initialize the UI immediately; do not leave disabled controls active.
    schedule->setEnabled(true);
    initCas->setEnabled(false);
    prune->setEnabled(false);
    sweepOrphans->setEnabled(false);
    m_parentSnapshots->setEnabled(false);
    // Never let an archive selected under another machine/repository be used
    // for a destructive prune or a staged restore after the context changes.
    const auto invalidateCatalog = [this] {
        ++m_contextRevision;
        m_archives->clear();
        m_machineSets->clear();
        m_pendingRestore.clear();
        m_pendingPruneArchive.clear();
        m_pendingPruneRepo.clear();
    };
    connect(m_target, &QLineEdit::textChanged, this, invalidateCatalog);
    connect(m_machineName, &QLineEdit::textChanged, this, invalidateCatalog);
    connect(m_backend, &QComboBox::currentIndexChanged, this, invalidateCatalog);
    connect(m_staging, &QLineEdit::textChanged, this, [this] {
        ++m_contextRevision;
        m_pendingRestore.clear();
    });
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
            static const QRegularExpression machinePattern(QStringLiteral("^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$"));
            if (!machinePattern.match(m_machineName->text()).hasMatch()) {
                QMessageBox::warning(this, tr("Invalid machine identity"),
                    tr("Enter a machine name using letters, digits, dots, underscores or hyphens (maximum 64 characters)."));
                return;
            }
            if (m_independentSend->isChecked()) {
                if (num == 0) {
                    QMessageBox::warning(this, tr("Invalid Btrfs source"),
                        tr("Select a readonly snapshot to back up."));
                    return;
                }
                if (QMessageBox::question(this, tr("Start background backup"),
                    tr("Harbor will select a verified CAS parent automatically. The systemd backup "
                       "continues if the window closes and can be resumed after a restart. Start now?"))
                       == QMessageBox::Yes) {
                    const QStringList params{
                        QStringLiteral("start"), QStringLiteral("--repo"), m_target->text(),
                        QStringLiteral("--machine"), m_machineName->text(),
                        QStringLiteral("--snapper-config"), m_configs->currentText(),
                        QStringLiteral("--snapper-number"), QString::number(num)};
                    launch(params, QStringLiteral("manual-job-start"),
                           QStringLiteral("btrfs-assistant-harbor-job"));
                }
                return;
            }
            const unsigned parentNum = m_parentSnapshots->currentData().toUInt();
            const QString current = snapperSourcePath(num);
            const QString parentSnapshot = parentNum > 0 ? snapperSourcePath(parentNum) : QString();
            QString parentArchive;
            if (parentNum > 0) {
                const QString prefix = QStringLiteral("m@%1@snap-%2-%3-")
                    .arg(m_machineName->text(), m_configs->currentText()).arg(parentNum);
                for (int i = 0; i < m_archives->count(); ++i) {
                    const QString candidate = m_archives->item(i)->data(Qt::UserRole).toString();
                    if (candidate.startsWith(prefix) && candidate > parentArchive)
                        parentArchive = candidate;
                }

            }
            const auto args = HarborRemote::casSendArguments(
                m_target->text(), m_configs->currentText(), num, current,
                parentNum > 0, parentSnapshot, parentNum, m_allowLocal->isChecked(),
                m_machineName->text(), parentArchive);
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
    connect(wholeBackup, &QPushButton::clicked, this, [this] {
        // Do not start a second disk-heavy backup during an existing send.
        if (!HarborProgress::active().isEmpty() ||
            !HarborProgress::machine().isEmpty()) {
            QMessageBox::information(this, tr("Backup already in progress"),
                tr("A backup is already running. Harbor will not start another one."));
            return;
        }
        if (m_target->text().isEmpty() || !QFileInfo(m_target->text()).isDir()) {
            const auto chosen = QFileDialog::getExistingDirectory(
                this, tr("Choose the mounted backup location"), m_target->text());
            if (chosen.isEmpty()) return;
            m_target->setText(chosen);
        }
        const auto profile = HarborRemote::profileId(QStringLiteral("whole-machine"),
                                                     m_target->text());
        const auto unit = QUuid::createUuid().toString(QUuid::WithoutBraces);
        bool parsed = false;
        const uint authenticatedUid = qEnvironmentVariable("PKEXEC_UID").toUInt(&parsed);
        const uint ownerUid = parsed && authenticatedUid > 0
            ? authenticatedUid : static_cast<uint>(getuid());
        const auto args = HarborRemote::wholeMachineStartArguments(
            m_target->text(), profile, unit, ownerUid);
        if (args.isEmpty()) {
            QMessageBox::warning(this, tr("Invalid machine backup destination"),
                tr("Choose a mounted remote backup directory before starting a whole-computer backup."));
            return;
        }
        // A backup is non-destructive; one click starts or safely resumes it.
        // The backend itself refuses an unmounted or changed destination.
        launch(args, QStringLiteral("whole-machine-start"), QStringLiteral("systemd-run"));
    });
    connect(wholeRestore, &QPushButton::clicked, this, [this] {
        if (m_target->text().isEmpty() || !QFileInfo(m_target->text()).isDir()) {
            const auto chosen = QFileDialog::getExistingDirectory(
                this, tr("Choose the mounted backup location"), m_target->text());
            if (chosen.isEmpty()) return;
            m_target->setText(chosen);
        }
        const auto args = HarborRemote::machineSetListArguments(m_target->text());
        if (args.isEmpty()) {
            QMessageBox::warning(this, tr("Choose backup destination"),
                tr("Select the mounted Cloud9 backup directory first."));
            return;
        }
        launch(args, QStringLiteral("whole-machine-catalog"));
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
        const QStringList names{"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"};
        QStringList days;
        if (m_frequency->currentData().toString() == QLatin1String("weekly")) {
            for (int i = 0; i < 7; ++i) if (m_weekdays[i]->isChecked()) days << names.at(i);
            if (days.isEmpty()) {
                QMessageBox::warning(this, tr("Invalid schedule"), tr("Choose at least one weekday."));
                return;
            }
        }
        const QStringList args = HarborRemote::scheduleInstallerArguments(
            m_configs->currentText(), m_target->text(), m_frequency->currentData().toString(),
            m_allowLocal->isChecked(), isCasMode(), isCasMode() ? m_machineName->text() : QString(),
            m_scheduleAt->time().toString(QStringLiteral("HH:mm")), days, m_catchUp->isChecked());
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
            m_configs->currentText(), m_target->text(), isCasMode(), isCasMode() ? m_machineName->text() : QString());
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
        const QString localMachinePrefix = QStringLiteral("m@%1@").arg(m_machineName->text());
        if (archive.startsWith(QStringLiteral("m@")) && !archive.startsWith(localMachinePrefix)) {
            QMessageBox::warning(this, tr("Archive belongs to another machine"),
                tr("Select the correct machine identity and refresh the repository list before pruning."));
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
#ifdef Q_OS_UNIX
    // Give each backup CLI and its btrfs send/receive children their own
    // session so a cancellation terminates the entire isolated process group.
    // Works on Qt 6.4 (Ubuntu 24.04) through Qt 6.10+. Run only
    // async-signal-safe POSIX calls between fork/vfork and exec.
    m_process->setChildProcessModifier([] {
        if (::setsid() == -1) _exit(127);
    });
#endif
    connect(jobJournal, &QPushButton::clicked, this, [this] {
        if (m_activeJobId.isEmpty()) {
            QMessageBox::information(this, tr("Backup journal"), tr("No active background backup."));
            return;
        }
        launch({QStringLiteral("-u"),
                QStringLiteral("btrfs-assistant-harbor-job@%1.service").arg(m_activeJobId),
                QStringLiteral("--no-pager"), QStringLiteral("-n"), QStringLiteral("80")},
               QStringLiteral("manual-job-log"), QStringLiteral("journalctl"));
    });
    connect(m_cancel, &QPushButton::clicked, this, [this] {
        if (m_process->state() == QProcess::NotRunning && !m_activeJobId.isEmpty()) {
            if (QMessageBox::question(this, tr("Cancel background backup"),
                    tr("Stop the systemd backup service? The completed CAS chunks will be preserved."))
                    == QMessageBox::Yes) {
                launch({QStringLiteral("cancel"), QStringLiteral("--id"), m_activeJobId},
                       QStringLiteral("manual-job-cancel"), QStringLiteral("btrfs-assistant-harbor-job"));
            }
            return;
        }
        if (m_process->state() == QProcess::NotRunning) return;
        m_cancelRequested = true;
        m_cancel->setEnabled(false);
        m_state->setText(tr("Stopping current operation..."));
#ifdef Q_OS_UNIX
        const pid_t processGroup = static_cast<pid_t>(m_process->processId());
        if (processGroup > 1) {
            ::kill(-processGroup, SIGTERM);
            QTimer::singleShot(3000, this, [this, processGroup] {
                if (m_process->state() != QProcess::NotRunning &&
                    static_cast<pid_t>(m_process->processId()) == processGroup) {
                    ::kill(-processGroup, SIGKILL);
                }
            });
        } else {
            m_process->terminate();
        }
#else
        m_process->terminate();
        QTimer::singleShot(3000, this, [this] {
            if (m_process->state() != QProcess::NotRunning) m_process->kill();
        });
#endif
    });
    connect(m_process, &QProcess::finished, this, &RemoteBackupWidget::actionFinished);
    connect(m_process, &QProcess::errorOccurred, this, [this](QProcess::ProcessError err) {
        if (err == QProcess::FailedToStart) {
            appendOutput(tr("Harbor CLI not found or failed to start: %1").arg(m_process->errorString()));
            m_state->setText(tr("Cannot start Harbor CLI"));
            m_send->setEnabled(true);
            m_cancel->setEnabled(false);
        }
    });
    connect(m_jobPoller, &QProcess::finished, this, [this](int exitCode, QProcess::ExitStatus status) {
        if (exitCode != 0 || status != QProcess::NormalExit) return;
        const auto json = QJsonDocument::fromJson(m_jobPoller->readAllStandardOutput());
        if (!json.isArray()) return;
        m_activeJobId.clear();
        QJsonObject newest;
        for (const auto &value : json.array()) {
            if (!value.isObject()) continue;
            const auto obj = value.toObject();
            if (obj.value(QStringLiteral("repository")).toString() != m_target->text() ||
                obj.value(QStringLiteral("machine")).toString() != m_machineName->text()) continue;
            if (newest.isEmpty() || obj.value(QStringLiteral("created")).toDouble() >
                                     newest.value(QStringLiteral("created")).toDouble()) newest = obj;
            const auto state = obj.value(QStringLiteral("state")).toString();
            if (state == QLatin1String("running") || state == QLatin1String("queued") ||
                state == QLatin1String("retrying")) m_activeJobId = obj.value(QStringLiteral("id")).toString();
        }
        const QJsonObject estimate = m_activeJobId.isEmpty()
            ? QJsonObject{} : HarborProgress::active(m_activeJobId);
        const QJsonObject machine = estimate.isEmpty() ? HarborProgress::machine() : QJsonObject{};
        m_progressDetails->setVisible(!estimate.isEmpty() || !machine.isEmpty());
        m_progressBar->setVisible(!estimate.isEmpty() || !machine.isEmpty());
        if (!machine.isEmpty()) {
            m_state->setText(tr("Whole-computer backup running in background"));
            m_progressDetails->setText(HarborProgress::machineOverview(machine));
            const auto percent = machine.value(QStringLiteral("estimated_percent"));
            if (percent.isDouble()) {
                m_progressBar->setRange(0, 1000);
                m_progressBar->setValue(qBound(0, qRound(percent.toDouble() * 10), 990));
                m_progressBar->setFormat(tr("Estimated progress: %p%"));
            } else m_progressBar->setRange(0, 0);
        } else if (!estimate.isEmpty()) {
            m_progressDetails->setText(HarborProgress::overview(estimate));
            const auto percentage = estimate.value(QStringLiteral("progress_percent_estimate"));
            if (percentage.isDouble()) {
                m_progressBar->setRange(0, 1000);
                m_progressBar->setValue(qBound(0, qRound(percentage.toDouble() * 10), 990));
                m_progressBar->setFormat(tr("Estimated progress: %p%"));
            } else {
                m_progressBar->setRange(0, 0);
            }
        }
        if (!m_activeJobId.isEmpty()) {
            m_cancel->setEnabled(m_process->state() == QProcess::NotRunning);
            m_send->setEnabled(false);
            m_state->setText(tr("Background backup: %1 — %2 bytes read")
                .arg(newest.value(QStringLiteral("state")).toString())
                .arg(QString::number(static_cast<qulonglong>(
                    newest.value(QStringLiteral("bytes_read")).toDouble()))));
        } else if (machine.isEmpty() && !newest.isEmpty() &&
                   m_process->state() == QProcess::NotRunning) {
            m_send->setEnabled(true);
            m_cancel->setEnabled(false);
            m_state->setText(tr("Last background backup: %1")
                .arg(newest.value(QStringLiteral("state")).toString()));
        }
    });
    auto *jobTimer = new QTimer(this);
    jobTimer->setInterval(4500);
    connect(jobTimer, &QTimer::timeout, this, &RemoteBackupWidget::pollManualJobs);
    jobTimer->start();
    QTimer::singleShot(0, this, &RemoteBackupWidget::pollManualJobs);
    refreshSnapshots();
}

void RemoteBackupWidget::pollManualJobs()
{
    if (m_jobPoller->state() != QProcess::NotRunning) return;
    const QString cli = QStandardPaths::findExecutable(QStringLiteral("btrfs-assistant-harbor-job"));
    if (cli.isEmpty() || !HarborRemote::trustedBackendExecutable(cli)) return;
    m_jobPoller->start(cli, {QStringLiteral("list")});
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
    // Bind every asynchronous result to the exact request context. UI inputs
    // remain editable while a backend runs, so a successful old response must
    // never populate a new machine's catalog or authorize a stale restore.
    m_requestRevision = m_contextRevision;
    m_requestRepo = m_target->text();
    m_requestMachine = m_machineName->text();
    m_requestCas = isCasMode();
    m_requestStaging = m_staging->text();
    m_requestArchive = selectedArchive();
    m_cancelRequested = false;
    m_cancel->setEnabled(true);
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
    m_cancel->setEnabled(false);
    if (m_cancelRequested) {
        m_cancelRequested = false;
        m_state->setText(tr("Operation cancelled; incomplete transfer must be resumed or retried."));
        return;
    }
    const bool ok = status == QProcess::NormalExit && code == 0;
    if (ok && m_purpose == QLatin1String("whole-machine-start")) {
        m_state->setText(tr("Whole-computer backup started in background. You may close Harbor."));
        return;
    }
    m_state->setText(ok ? tr("Operation finished: %1").arg(m_purpose)
                        : tr("Operation failed: %1 (exit %2)").arg(m_purpose).arg(code));
    if (!ok) return;
    if (m_purpose == QLatin1String("whole-machine-catalog")) {
        if (m_requestRepo != m_target->text() || m_requestRevision != m_contextRevision)
            return;
        QJsonParseError parse{};
        const auto payload = QJsonDocument::fromJson(m_stdout, &parse);
        if (parse.error != QJsonParseError::NoError || !payload.isArray()) {
            QMessageBox::warning(this, tr("Backup catalog unavailable"),
                                 tr("Could not load verified computer backups."));
            return;
        }
        QDialog dialog(this);
        dialog.setWindowTitle(tr("Restore a computer"));
        auto *layout = new QVBoxLayout(&dialog);
        auto *note = new QLabel(tr("Choose a complete dated machine backup. "
            "The first step receives all volumes into an empty Btrfs staging area. "
            "Boot restoration is separate and must be verified."), &dialog);
        note->setWordWrap(true);
        layout->addWidget(note);
        auto *form = new QFormLayout();
        auto *machines = new QComboBox(&dialog);
        auto *dates = new QComboBox(&dialog);
        auto *policy = new QComboBox(&dialog);
        auto *newHost = new QLineEdit(&dialog);
        machines->setObjectName(QStringLiteral("harborRestoreComputer"));
        dates->setObjectName(QStringLiteral("harborRestoreComputerDate"));
        policy->setObjectName(QStringLiteral("harborRestoreHostPolicy"));
        policy->addItem(tr("Keep original machine name"), QStringLiteral("original"));
        policy->addItem(tr("Keep current installation name"), QStringLiteral("installed"));
        policy->addItem(tr("Use a different name"), QStringLiteral("custom"));
        form->addRow(tr("Computer"), machines);
        form->addRow(tr("Backup date"), dates);
        form->addRow(tr("Name after restoration"), policy);
        form->addRow(tr("Custom name"), newHost);
        layout->addLayout(form);
        QJsonArray complete;
        for (const auto &v : payload.array()) {
            const auto obj = v.toObject();
            const auto name = obj.value(QStringLiteral("machine_name")).toString();
            const auto state = obj.value(QStringLiteral("status")).toString();
            if (name.isEmpty() || state != QLatin1String("completed_btrfs_and_boot_files"))
                continue;
            complete.append(obj);
            if (machines->findText(name) < 0) machines->addItem(name);
        }
        const auto reloadDates = [&] {
            dates->clear();
            for (const auto &v : complete) {
                const auto obj = v.toObject();
                if (obj.value(QStringLiteral("machine_name")).toString() != machines->currentText())
                    continue;
                const auto created = QDateTime::fromString(
                    obj.value(QStringLiteral("created_utc")).toString(), Qt::ISODate);
                dates->addItem(created.isValid()
                    ? created.toLocalTime().toString(QStringLiteral("yyyy-MM-dd HH:mm"))
                    : obj.value(QStringLiteral("created_utc")).toString(),
                    obj.value(QStringLiteral("set_id")).toString());
            }
        };
        connect(machines, &QComboBox::currentTextChanged, &dialog, reloadDates);
        connect(policy, &QComboBox::currentIndexChanged, &dialog,
                [=] { newHost->setEnabled(policy->currentData() == QLatin1String("custom")); });
        newHost->setEnabled(false);
        reloadDates();
        auto *buttons = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel, &dialog);
        buttons->button(QDialogButtonBox::Ok)->setText(tr("Verify backup and prepare recovery"));
        buttons->button(QDialogButtonBox::Ok)->setEnabled(!complete.isEmpty());
        layout->addWidget(buttons);
        if (complete.isEmpty())
            note->setText(tr("No complete machine backup is available here yet. "
                             "A single Snapper root snapshot is not a whole-computer backup."));
        connect(buttons, &QDialogButtonBox::rejected, &dialog, &QDialog::reject);
        connect(buttons, &QDialogButtonBox::accepted, &dialog, &QDialog::accept);
        if (dialog.exec() != QDialog::Accepted) return;
        static const QRegularExpression allowed(QStringLiteral("^[A-Za-z0-9][A-Za-z0-9-]{0,62}$"));
        const auto choice = policy->currentData().toString();
        const auto name = choice == QLatin1String("original") ? machines->currentText()
            : choice == QLatin1String("installed") ? QSysInfo::machineHostName()
            : newHost->text().trimmed();
        if (!allowed.match(name).hasMatch()) {
            QMessageBox::warning(this, tr("Invalid computer name"),
                                 tr("Use 1–63 ASCII letters, digits or hyphens."));
            return;
        }
        const auto id = dates->currentData().toString();
        QString recoveryStaging;
        QString error;
        if (!HarborStaging::prepare(id, &recoveryStaging, &error)) {
            QMessageBox::warning(this, tr("Recovery preparation refused"),
                                 tr("Could not prepare a safe Btrfs recovery: %1").arg(error));
            return;
        }
        const auto args = HarborRemote::machineSetPreviewArguments(
            m_target->text(), id, recoveryStaging);
        if (args.isEmpty()) {
            QMessageBox::warning(this, tr("Invalid recovery selection"),
                                 tr("Choose a completed computer backup and a safe absolute staging directory."));
            return;
        }
        m_computerRecoveryId = id;
        m_computerRecoveryName = name;
        m_computerRecoveryPolicy = choice;
        m_computerRecoveryStaging = recoveryStaging;
        m_computerRecoveryRepository = m_target->text();
        launch(args, QStringLiteral("whole-machine-restore-preview"));
        return;
    }
    if (m_purpose == QLatin1String("whole-machine-restore-preview")) {
        if (m_requestRepo != m_target->text() ||
            m_computerRecoveryRepository != m_target->text() ||
            m_requestRevision != m_contextRevision ||
            m_computerRecoveryId.isEmpty()) return;
        HarborMachineProtocol::RestorePreview plan;
        QString error;
        if (!HarborMachineProtocol::preview(m_stdout, m_computerRecoveryStaging, &plan, &error)) {
            QMessageBox::warning(this, tr("Computer recovery refused"),
                                 tr("Backup verification failed: %1").arg(error));
            return;
        }
        if (QMessageBox::question(this, tr("Receive a complete computer backup"),
            tr("Verified: %1 Btrfs volumes and %2 EFI archives. "
               "Recover these volumes to the EMPTY staging directory? "
               "The running CachyOS installation will NOT be overwritten. "
               "Selected future machine name: %3.").arg(plan.volumesCount)
              .arg(plan.bootFiles).arg(m_computerRecoveryName)) != QMessageBox::Yes) return;
        const auto args = HarborRemote::machineSetPreviewArguments(
            m_target->text(), m_computerRecoveryId, m_computerRecoveryStaging);
        QStringList confirmed = args;
        confirmed << QStringLiteral("--confirm");
        launch(confirmed, QStringLiteral("whole-machine-restore-staged"));
        return;
    }
    if (m_purpose == QLatin1String("whole-machine-restore-staged")) {
        QMessageBox::information(this, tr("Files safely recovered"),
            tr("All backup volumes have been received into the staging directory. "
               "The bootable machine activation phase still requires an offline recovery environment "
               "and is not yet certified for LUKS/Limine."));
        return;
    }
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
                tr("%1 — %2 Btrfs volumes, %3 boot-file sets — %4 — NOT bootable")
                    .arg(record.id).arg(record.volumes).arg(record.bootFiles)
                    .arg(record.complete ? tr("QA staging preview available")
                                         : tr("INCOMPLETE: %1").arg(record.status)),
                m_machineSets);
            if (!record.complete) {
                item->setFlags(item->flags() & ~Qt::ItemIsSelectable);
                item->setToolTip(tr("Incomplete machine backup set: preview restore unavailable."));
            }
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
        if (m_requestRevision != m_contextRevision ||
            !HarborRemote::selectionContextMatches(m_requestRepo, m_requestMachine, m_requestCas,
                                                    m_target->text(), m_machineName->text(), isCasMode()) ||
            m_requestRepo != m_pendingPruneRepo ||
            (!m_pendingPruneArchive.isEmpty() &&
             (m_requestArchive != m_pendingPruneArchive ||
              selectedArchive() != m_pendingPruneArchive))) {
            appendOutput(tr("Backup context changed; refresh archives before pruning."));
            return;
        }
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
        if (m_requestRevision != m_contextRevision ||
            !HarborRemote::selectionContextMatches(m_requestRepo, m_requestMachine, m_requestCas,
                                                    m_target->text(), m_machineName->text(), isCasMode())) {
            appendOutput(tr("Backup context changed; refusing stale archive catalog."));
            return;
        }
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
            // One object pool for all machines. UI is scoped to the selected
            // machine; legacy archives are still visible for compatibility.
            const QString activePrefix = QStringLiteral("m@%1@").arg(m_machineName->text());
            if (isCasMode() && name.startsWith(QStringLiteral("m@")) && !name.startsWith(activePrefix))
                continue;
            auto *item = new QListWidgetItem(name, m_archives);
            item->setData(Qt::UserRole, name);
        }
    }
    if (m_purpose == QLatin1String("list-transfers")) {
        if (m_requestRevision != m_contextRevision ||
            !HarborRemote::selectionContextMatches(m_requestRepo, m_requestMachine, m_requestCas,
                                                    m_target->text(), m_machineName->text(), isCasMode())) {
            appendOutput(tr("Backup context changed; refusing stale archive catalog."));
            return;
        }
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
        if (m_requestRevision != m_contextRevision ||
            !HarborRemote::selectionContextMatches(m_requestRepo, m_requestMachine, m_requestCas,
                                                    m_target->text(), m_machineName->text(), isCasMode()) ||
            m_requestStaging != m_staging->text() ||
            m_requestArchive != selectedArchive() || m_pendingRestore.isEmpty()) {
            appendOutput(tr("Backup or recovery destination changed; refusing stale restore preview."));
            return;
        }
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
        if (m_requestRevision != m_contextRevision ||
            !HarborRemote::selectionContextMatches(m_requestRepo, m_requestMachine, m_requestCas,
                                                    m_target->text(), m_machineName->text(), isCasMode()) ||
            m_requestStaging != m_staging->text() ||
            m_requestArchive != selectedArchive() || m_pendingRestore.isEmpty()) {
            appendOutput(tr("Backup or recovery destination changed; refusing stale restore preview."));
            return;
        }
        if (QMessageBox::question(this, tr("Confirm recovery"),
                tr("Dry-run successful. Restore the selected snapshot into the staging directory? "
                   "Existing system subvolumes will not be replaced.")) == QMessageBox::Yes) {
            QStringList apply = m_pendingRestore;
            apply.removeAll(QStringLiteral("--dry-run"));
            launch(apply, QStringLiteral("restore"));
        }
    }
}
