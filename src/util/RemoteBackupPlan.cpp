#include "util/RemoteBackupPlan.h"
#include <QDir>
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
