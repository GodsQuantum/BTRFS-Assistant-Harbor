#include "util/RemoteBackupPlan.h"
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <sys/stat.h>
#include <QRegularExpression>
#include <QUuid>
namespace {
bool safeConfig(const QString &config) {
    static const QRegularExpression pattern(QStringLiteral("^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$"));
    return pattern.match(config).hasMatch();
}
bool safeArchive(const QString &name) {
    static const QRegularExpression pattern(QStringLiteral("^[A-Za-z0-9][A-Za-z0-9_.-]{0,199}$"));
    return pattern.match(name).hasMatch();
}
bool safePath(const QString &path, bool rootAllowed = false) {
    return !path.isEmpty() && path.startsWith(QChar(0x2f)) &&
           QDir::cleanPath(path) == path && (rootAllowed || path != QLatin1String("/")) &&
           !path.contains(QLatin1Char('\n')) && !path.contains(QLatin1Char('\r'));
}
}
namespace HarborRemote {
QString profileId(const QString &config, const QString &target) {
    if (!safeConfig(config) || !safePath(target)) return {};
    static const QUuid namespaceId(QStringLiteral("{18e0b70e-dced-4a95-9179-8b45efbd3f51}"));
    return QUuid::createUuidV5(namespaceId, (config + QLatin1Char('\n') + target).toUtf8()).toString(QUuid::WithoutBraces);
}
QString archiveName(const QString &config, unsigned number) {
    if (!safeConfig(config) || number == 0) return {};
    return QStringLiteral("snap-%1-%2").arg(config).arg(number);
}
QStringList sendArguments(const QString &config, unsigned number, const QString &target, bool allowLocal) {
    const QString name = archiveName(config, number);
    const QString profile = profileId(config, target);
    if (name.isEmpty() || profile.isEmpty()) return {};
    QStringList out{QStringLiteral("raw"), QStringLiteral("checkpoint-v2"), QStringLiteral("start"),
                    QStringLiteral("--target"), target, QStringLiteral("--source-mode"), QStringLiteral("selected-snapper"),
                    QStringLiteral("--snapper-config"), config, QStringLiteral("--snapper-number"), QString::number(number),
                    QStringLiteral("--name"), name, QStringLiteral("--profile-id"), profile,
                    QStringLiteral("--experimental")};
    if (allowLocal) out << QStringLiteral("--allow-local");
    return out;
}
QStringList scheduleArguments(const QString &config, const QString &target, bool allowLocal) {
    const QString profile = profileId(config, target);
    if (profile.isEmpty()) return {};
    QStringList out{QStringLiteral("raw"), QStringLiteral("checkpoint-v2"), QStringLiteral("schedule-run"),
                    QStringLiteral("--target"), target, QStringLiteral("--snapper-config"), config,
                    QStringLiteral("--profile-id"), profile, QStringLiteral("--name-prefix"), QStringLiteral("snap-") + config,
                    QStringLiteral("--experimental")};
    if (allowLocal) out << QStringLiteral("--allow-local");
    return out;
}
QStringList verifyArguments(const QString &target, const QString &archive) {
    if (!safePath(target) || !safeArchive(archive)) return {};
    return {QStringLiteral("raw"), QStringLiteral("verify"), target, QStringLiteral("--snapshot"), archive, QStringLiteral("--json")};
}
QStringList previewRestoreArguments(const QString &target, const QString &archive, const QString &staging) {
    if (!safePath(target) || !safeArchive(archive) || !safePath(staging)) return {};
    return {QStringLiteral("restore"), QStringLiteral("raw://") + target, staging, QStringLiteral("--snapshot"), archive,
            QStringLiteral("--dry-run"), QStringLiteral("--fs-checks"), QStringLiteral("strict")};
}
QStringList listArguments(const QString &target) {
    if (!safePath(target)) return {};
    return {QStringLiteral("raw"), QStringLiteral("list"), target, QStringLiteral("--json")};
}
}


namespace HarborRemote {
QStringList transfersArguments(const QString &target) {
    if (!safePath(target)) return {};
    return {QStringLiteral("raw"), QStringLiteral("checkpoint-v2"), QStringLiteral("list"), QStringLiteral("--target"), target};
}
QStringList resumeArguments(const QString &target, const QString &archive, const QString &transferId, bool allowLocal) {
    const QUuid uuid(transferId);
    if (!safePath(target) || !safeArchive(archive) || uuid.isNull() ||
        uuid.toString(QUuid::WithoutBraces) != transferId) return {};
    QStringList args{QStringLiteral("raw"), QStringLiteral("checkpoint-v2"), QStringLiteral("resume"),
                     QStringLiteral("--target"), target, QStringLiteral("--name"), archive,
                     QStringLiteral("--transfer-id"), transferId, QStringLiteral("--experimental")};
    if (allowLocal) args << QStringLiteral("--allow-local");
    return args;
}
}


namespace HarborRemote {
bool trustedBackendExecutable(const QString &path) {
    if (!safePath(path)) return false;
    QFileInfo info(path);
    if (!info.exists() || !info.isFile() || !info.isExecutable()) return false;
    const QString realPath = info.canonicalFilePath();
    if (!(realPath.startsWith(QLatin1String("/usr/bin/")) ||
          realPath.startsWith(QLatin1String("/usr/local/bin/")))) return false;
    const auto safeOwnerAndMode = [](const QString &candidate, bool executable) {
        struct stat st {};
        const QByteArray encoded = QFile::encodeName(candidate);
        if (::stat(encoded.constData(), &st) != 0 || st.st_uid != 0 || (st.st_mode & 0022) != 0)
            return false;
        if (executable && (!S_ISREG(st.st_mode) || (st.st_mode & 0111) == 0))
            return false;
        if (!executable && !S_ISDIR(st.st_mode))
            return false;
        return true;
    };
    if (!safeOwnerAndMode(realPath, true)) return false;
    // Reject replaced/bad permissions on directories controlling the executable.
    QString parent = QFileInfo(realPath).absolutePath();
    while (!parent.isEmpty()) {
        if (!safeOwnerAndMode(parent, false)) return false;
        if (parent == QLatin1String("/")) break;
        parent = QFileInfo(parent).absolutePath();
    }
    return true;
}
}

namespace HarborRemote {
QStringList casInitArguments(const QString &repo, bool allowLocal) {
    if (!safePath(repo)) return {};
    QStringList args{QStringLiteral("init"), QStringLiteral("--repo"), repo};
    if (allowLocal) args << QStringLiteral("--allow-local");
    return args;
}
QStringList casListArguments(const QString &repo) {
    if (!safePath(repo)) return {};
    return {QStringLiteral("list"), QStringLiteral("--repo"), repo};
}
QStringList casSendArguments(const QString &repo, const QString &config, unsigned number,
                             const QString &snapshot, bool incremental,
                             const QString &parentSnapshot, unsigned parentNumber, bool allowLocal) {
    const QString name = archiveName(config, number);
    if (name.isEmpty() || !safePath(repo) || !safePath(snapshot)) return {};
    QStringList args{QStringLiteral("send"), QStringLiteral("--repo"), repo,
                     QStringLiteral("--name"), name,
                     QStringLiteral("--snapshot"), snapshot,
                     QStringLiteral("--experimental"), QStringLiteral("--retries"), QStringLiteral("5")};
    if (incremental) {
        const QString parentName = archiveName(config, parentNumber);
        if (parentName.isEmpty() || !safePath(parentSnapshot) ||
            parentSnapshot == snapshot || parentNumber >= number) return {};
        args << QStringLiteral("--parent") << parentSnapshot
             << QStringLiteral("--parent-archive") << parentName;
    }
    if (allowLocal) args << QStringLiteral("--allow-local");
    return args;
}
QStringList casVerifyArguments(const QString &repo, const QString &name) {
    if (!safePath(repo) || !safeArchive(name)) return {};
    return {QStringLiteral("verify-stream"), QStringLiteral("--repo"), repo,
            QStringLiteral("--name"), name};
}
QStringList casPreviewArguments(const QString &repo, const QString &name, const QString &staging) {
    if (!safePath(repo) || !safeArchive(name) || !safePath(staging)) return {};
    return {QStringLiteral("receive"), QStringLiteral("--repo"), repo,
            QStringLiteral("--name"), name, QStringLiteral("--staging"), staging, QStringLiteral("--preview")};
}
QStringList casConfirmArguments(const QString &repo, const QString &name, const QString &staging) {
    if (!safePath(repo) || !safeArchive(name) || !safePath(staging)) return {};
    return {QStringLiteral("receive"), QStringLiteral("--repo"), repo,
            QStringLiteral("--name"), name, QStringLiteral("--staging"), staging, QStringLiteral("--confirm")};
}
}
