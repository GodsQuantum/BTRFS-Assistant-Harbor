#include "ui/RemoteBackupWidget.h"
#include "util/RemoteBackupPlan.h"
#include "util/Snapper.h"

#include <QCheckBox>
#include <QComboBox>
#include <QDateTime>
#include <QFileDialog>
#include <QFormLayout>
#include <QGroupBox>
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
#include <QStandardPaths>
#include <QVBoxLayout>

RemoteBackupWidget::RemoteBackupWidget(Snapper *snapper, QWidget *parent)
    : QWidget(parent), m_snapper(snapper), m_configs(new QComboBox(this)),
      m_snapshots(new QComboBox(this)), m_target(new QLineEdit(this)),
      m_staging(new QLineEdit(this)), m_frequency(new QComboBox(this)), m_allowLocal(new QCheckBox(tr("Allow explicitly selected local destination"), this)),
      m_archives(new QListWidget(this)), m_log(new QPlainTextEdit(this)),
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
    form->addRow(tr("Snapper configuration"), m_configs);
    form->addRow(tr("Readonly snapshot"), snapshotRow);
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

    auto *actions = new QHBoxLayout();
    auto *inventory = new QPushButton(tr("List remote backups"), this);
    auto *schedule = new QPushButton(tr("Enable schedule"), this);
    auto *verify = new QPushButton(tr("Verify selected archive"), this);
    auto *recover = new QPushButton(tr("Preview recovery"), this);
    actions->addWidget(m_send);
    actions->addWidget(inventory);
    actions->addWidget(verify);
    actions->addWidget(recover);
    actions->addWidget(schedule);
    layout->addLayout(actions);
    layout->addWidget(new QLabel(tr("Stored snapshots — select one to verify or recover"), this));
    m_archives->setMinimumHeight(100);
    layout->addWidget(m_archives);
    layout->addWidget(m_state);
    m_log->setReadOnly(true);
    m_log->setMaximumBlockCount(1500);
    m_log->setPlaceholderText(tr("Transfers run asynchronously; process output appears here."));
    layout->addWidget(m_log, 1);

    if (m_snapper != nullptr) {
        m_configs->addItems(m_snapper->configs());
    }
    connect(m_configs, &QComboBox::currentTextChanged, this, [this] { refreshSnapshots(); });
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
        const auto name = HarborRemote::archiveName(m_configs->currentText(), num);
        const auto args = HarborRemote::sendArguments(m_configs->currentText(), num, m_target->text(), m_allowLocal->isChecked());
        if (args.isEmpty()) { QMessageBox::warning(this, tr("Invalid selection"), tr("Select a valid Snapper snapshot and an absolute destination.")); return; }
        if (QMessageBox::question(this, tr("Start backup"), tr("Send snapshot %1 to %2?").arg(name, m_target->text())) == QMessageBox::Yes)
            launch(args, QStringLiteral("send"));
    });
    connect(inventory, &QPushButton::clicked, this, &RemoteBackupWidget::listArchives);
    connect(schedule, &QPushButton::clicked, this, [this] {
        const auto args = HarborRemote::scheduleArguments(m_configs->currentText(), m_target->text(), m_allowLocal->isChecked());
        if (args.isEmpty()) {
            QMessageBox::warning(this, tr("Invalid schedule"), tr("Select a valid Snapper config and destination."));
            return;
        }
        if (QMessageBox::question(this, tr("Install systemd timer"),
                tr("Install and enable an automatic %1 transfer for %2? No snapshot is created now.")
                    .arg(m_frequency->currentText(), m_configs->currentText())) != QMessageBox::Yes) return;
        QStringList install{QStringLiteral("install"), QStringLiteral("--snapper-config"), m_configs->currentText(),
                            QStringLiteral("--target"), m_target->text(), QStringLiteral("--frequency"),
                            m_frequency->currentData().toString(), QStringLiteral("--enable")};
        if (m_allowLocal->isChecked()) install << QStringLiteral("--allow-local");
        launch(install, QStringLiteral("schedule"), QStringLiteral("btrfs-assistant-harbor-schedule"));
    });
    connect(verify, &QPushButton::clicked, this, [this] {
        const auto args = HarborRemote::verifyArguments(m_target->text(), selectedArchive());
        if (args.isEmpty()) { QMessageBox::warning(this, tr("Missing archive"), tr("Select a valid archive and destination.")); return; }
        launch(args, QStringLiteral("verify"));
    });
    connect(recover, &QPushButton::clicked, this, [this] {
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
        appendOutput(QString::fromUtf8(m_process->readAllStandardError()));
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

void RemoteBackupWidget::refreshSnapshots()
{
    m_snapshots->clear();
    if (m_snapper == nullptr) return;
    const auto snapshots = m_snapper->snapshots(m_configs->currentText());
    for (const auto &snapshot : snapshots) {
        if (snapshot.number == 0) continue;
        const QString label = QStringLiteral("#%1 — %2 — %3")
                                  .arg(snapshot.number)
                                  .arg(snapshot.time.toString(Qt::ISODate), snapshot.desc);
        m_snapshots->addItem(label, snapshot.number);
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
    if (cli.isEmpty()) {
        QMessageBox::critical(this, tr("Missing engine"), tr("Required backend executable not found: %1").arg(executable));
        return;
    }
    m_purpose = purpose;
    m_stdout.clear();
    m_send->setEnabled(false);
    m_state->setText(tr("Running: %1").arg(purpose));
    m_process->setProgram(cli);
    m_process->setArguments(arguments);
    m_process->start();
}

void RemoteBackupWidget::listArchives()
{
    const auto args = HarborRemote::listArguments(m_target->text());
    if (args.isEmpty()) {
        QMessageBox::warning(this, tr("Invalid destination"), tr("Choose an absolute backup directory."));
        return;
    }
    launch(args, QStringLiteral("list"));
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
