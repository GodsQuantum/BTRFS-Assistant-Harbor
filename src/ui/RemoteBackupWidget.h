#pragma once

#include <QProcess>
#include <QElapsedTimer>
#include <QWidget>
#include <functional>

class Snapper;
class QCheckBox;
class QComboBox;
class QLineEdit;
class QTimeEdit;
class QListWidget;
class QPushButton;
class QPlainTextEdit;
class QLabel;
class QProgressBar;

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
    QLineEdit *m_machineName;
    QLineEdit *m_staging;
    QComboBox *m_frequency;
    QTimeEdit *m_scheduleAt;
    QCheckBox *m_weekdays[7]{};
    QCheckBox *m_catchUp;
    QCheckBox *m_independentSend;
    QCheckBox *m_allowLocal;
    QListWidget *m_archives;
    QListWidget *m_machineSets;
    QPlainTextEdit *m_log;
    QLabel *m_state;
    QLabel *m_progressDetails;
    QProgressBar *m_progressBar;
    QPushButton *m_send;
    QPushButton *m_cancel;
    bool m_cancelRequested = false;
    QProcess *m_process;
    QProcess *m_jobPoller;
    QString m_activeJobId;
    void pollManualJobs();
    QByteArray m_stdout;
    QByteArray m_stderrBuffer;
    QElapsedTimer m_transferTimer;
    QString m_purpose;
    QStringList m_pendingRestore;
    QString m_pendingPruneArchive;
    QString m_pendingPruneRepo;
    QString m_requestRepo;
    QString m_requestMachine;
    QString m_requestStaging;
    QString m_requestArchive;
    bool m_requestCas = false;
    quint64 m_contextRevision = 0;
    quint64 m_requestRevision = 0;
    QString m_machineListRepo;
    QString m_machinePreviewRepo;
    QString m_machinePreviewStaging;
    QString m_machinePreviewId;
};
