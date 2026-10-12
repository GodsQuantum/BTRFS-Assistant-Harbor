#pragma once

#include <QProcess>
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
    void launch(const QStringList &arguments, const QString &purpose, const QString &executable = QStringLiteral("btrfs-backup-ng"));
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
    QPlainTextEdit *m_log;
    QLabel *m_state;
    QPushButton *m_send;
    QProcess *m_process;
    QByteArray m_stdout;
    QString m_purpose;
    QStringList m_pendingRestore;
};
