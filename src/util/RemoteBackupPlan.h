#pragma once
#include <QString>
#include <QStringList>
namespace HarborRemote {
// Exact request context, required before showing an asynchronous listing or
// using a prune/restore preview; never compare only the archive filename.
bool selectionContextMatches(const QString &repo, const QString &machine, bool cas,
                             const QString &currentRepo, const QString &currentMachine, bool currentCas);
QString profileId(const QString &config, const QString &target);
QString profileIdForEngine(const QString &config, const QString &target, bool cas, const QString &machine = QString());
QStringList scheduleInstallerArguments(const QString &config, const QString &target,
                                       const QString &frequency, bool allowLocal, bool cas, const QString &machine = QString(),
                                        const QString &at = QString(), const QStringList &weekdays = {},
                                        bool catchUp = true);
QString archiveName(const QString &config, unsigned number);
QStringList sendArguments(const QString &config, unsigned number, const QString &target, bool allowLocal);
QStringList scheduleArguments(const QString &config, const QString &target, bool allowLocal);
QStringList verifyArguments(const QString &target, const QString &archive);
QStringList previewRestoreArguments(const QString &target, const QString &archive, const QString &staging);
QStringList listArguments(const QString &target);
bool trustedBackendExecutable(const QString &path);
// Legacy checkpoint-v2 machine sets: read-only catalog and staged-restore preview.
QStringList machineInventoryArguments();
// Full-machine checkpoint-v2 snapshots, external EFI, background systemd unit.
// This is NOT the root-only CAS snapshot button or a new stream engine.
QStringList wholeMachineStartArguments(const QString &target, const QString &profileId,
                                       const QString &unitId);
  // native readonly Btrfs/EFI coverage audit
QStringList machineSetListArguments(const QString &target);
QStringList machineSetPreviewArguments(const QString &target, const QString &setId, const QString &staging);
QStringList casInitArguments(const QString &repo, bool allowLocal);
QStringList casListArguments(const QString &repo);
QStringList casPrunePreviewArguments(const QString &repo, const QString &archive = QString());
QStringList casPruneConfirmArguments(const QString &repo, const QString &archive, const QString &planSha256);
QStringList casSendArguments(const QString &repo, const QString &config, unsigned number,
                             const QString &snapshot, bool incremental,
                             const QString &parentSnapshot, unsigned parentNumber, bool allowLocal,
                             const QString &machine = QString(), const QString &parentArchive = QString());
QStringList casVerifyArguments(const QString &repo, const QString &name);
QStringList casPreviewArguments(const QString &repo, const QString &name, const QString &staging);
QStringList casConfirmArguments(const QString &repo, const QString &name, const QString &staging);
QStringList transfersArguments(const QString &target);
QStringList resumeArguments(const QString &target, const QString &archive, const QString &transferId, bool allowLocal);
}
