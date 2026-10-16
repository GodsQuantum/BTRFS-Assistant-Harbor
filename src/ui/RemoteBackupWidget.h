#pragma once

#include <QProcess>
#include <QElapsedTimer>
#include <QWidget>
#include <functional>

class Snapper;
class QCheckBox;
class QComboBox;
class QLineEdit;
class QListWidget;
class QPushButton;
class QPlainTextEdit;
class QLabel;

class RemoteBackupWidget final : public QWidget {
    Q_OBJECT
public:
    explicit RemoteBackupWidget(Snapper *snapper, QWidget *parent = nullptr);
private:
    void refreshSnapshots();
    bool isCasMode() const;
    QString snapperSourcePath(unsigned number) const;
    void launch(const QStringList &arguments, const QString &purpose, const QString &executable = QStringLiteral("harbor-checkpoint-v2"));
    void listArchives();
    void listTransfers();
    void appendOutput(const QString &output);
    void actionFinished(int exitCode, QProcess::ExitStatus exitStatus);
    QString selectedArchive() const;
    Snapper *m_snapper;
    QComboBox *m_backend;
    QComboBox *m_parentSnapshots;
    QComboBox *m_configs;
    QComboBox *m_snapshots;
    QLineEdit *m_target;
    QLineEdit *m_staging;
    QComboBox *m_frequency;
    QCheckBox *m_allowLocal;
    QListWidget *m_archives;
    QListWidget *m_machineSets;
    QPlainTextEdit *m_log;
    QLabel *m_state;
    QPushButton *m_send;
    QPushButton *m_cancel;
    bool m_cancelRequested = false;
    QProcess *m_process;
    QByteArray m_stdout;
    QByteArray m_stderrBuffer;
    QElapsedTimer m_transferTimer;
    QString m_purpose;
    QStringList m_pendingRestore;
    QString m_pendingPruneArchive;
    QString m_pendingPruneRepo;
    QString m_machineListRepo;
    QString m_machinePreviewRepo;
    QString m_machinePreviewStaging;
    QString m_machinePreviewId;
};
