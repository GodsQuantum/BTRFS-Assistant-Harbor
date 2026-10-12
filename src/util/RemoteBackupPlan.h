#pragma once
#include <QString>
#include <QStringList>
namespace HarborRemote {
QString profileId(const QString &config, const QString &target);
QString archiveName(const QString &config, unsigned number);
QStringList sendArguments(const QString &config, unsigned number, const QString &target, bool allowLocal);
QStringList scheduleArguments(const QString &config, const QString &target, bool allowLocal);
QStringList verifyArguments(const QString &target, const QString &archive);
QStringList previewRestoreArguments(const QString &target, const QString &archive, const QString &staging);
QStringList listArguments(const QString &target);
bool trustedBackendExecutable(const QString &path);
QStringList casInitArguments(const QString &repo, bool allowLocal);
QStringList casListArguments(const QString &repo);
QStringList casSendArguments(const QString &repo, const QString &config, unsigned number,
                             const QString &snapshot, bool incremental,
                             const QString &parentSnapshot, unsigned parentNumber, bool allowLocal);
QStringList casVerifyArguments(const QString &repo, const QString &name);
QStringList casPreviewArguments(const QString &repo, const QString &name, const QString &staging);
QStringList casConfirmArguments(const QString &repo, const QString &name, const QString &staging);
QStringList transfersArguments(const QString &target);
QStringList resumeArguments(const QString &target, const QString &archive, const QString &transferId, bool allowLocal);
}
