#include "util/MachineSetProtocol.h"
#include <QDir>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonParseError>
#include <QRegularExpression>
#include <QSet>
#include <QUuid>
namespace {
bool fail(QString *error, const QString &why) {
    if (error) *error = why;
    return false;
}
bool canonicalUuid(const QString &value) {
    const QUuid id(value);
    return !id.isNull() && id.toString(QUuid::WithoutBraces) == value;
}
bool absoluteClean(const QString &value) {
    if (value.isEmpty() || !value.startsWith(QLatin1Char('/')) ||
        value.contains(QLatin1Char('\n')) || value.contains(QLatin1Char('\r')) ||
        value.contains(QChar(0)) || value.size() > 2048)
        return false;
    return QDir::cleanPath(value) == value;
}
bool archiveName(const QString &value) {
    static const QRegularExpression pattern(
        QStringLiteral("^[A-Za-z0-9][A-Za-z0-9_.-]{0,199}$"));
    return pattern.match(value).hasMatch();
}
bool jsonDoc(const QByteArray &bytes, QJsonDocument *doc, QString *error) {
    if (bytes.size() > 1024 * 1024)
        return fail(error, QStringLiteral("Backend response exceeds 1 MiB"));
    QJsonParseError parse{};
    *doc = QJsonDocument::fromJson(bytes, &parse);
    if (parse.error != QJsonParseError::NoError)
        return fail(error, QStringLiteral("Backend returned malformed JSON"));
    return true;
}
}
namespace HarborMachineProtocol {
bool catalog(const QByteArray &response, QList<BackupSet> *result, QString *error) {
    if (!result) return fail(error, QStringLiteral("No catalog output"));
    QJsonDocument doc;
    if (!jsonDoc(response, &doc, error)) return false;
    if (!doc.isArray() || doc.array().size() > 1024)
        return fail(error, QStringLiteral("Expected machine-set array of at most 1024 entries"));
    QList<BackupSet> found;
    QSet<QString> seen;
    for (const QJsonValue &row : doc.array()) {
        if (!row.isObject())
            return fail(error, QStringLiteral("Machine-set row is not an object"));
        const auto item = row.toObject();
        const auto id = item.value(QStringLiteral("set_id")).toString();
        const auto status = item.value(QStringLiteral("status")).toString();
        const auto members = item.value(QStringLiteral("members"));
        const auto boot = item.value(QStringLiteral("boot_partitions"));
        static const QRegularExpression safeStatus(QStringLiteral("^[a-z_]{1,64}$"));
        const bool complete = status == QLatin1String("completed_btrfs_only") ||
                              status == QLatin1String("completed_btrfs_and_boot_files");
        if (!canonicalUuid(id) || seen.contains(id) ||
            !safeStatus.match(status).hasMatch() || !members.isDouble() || !boot.isDouble())
            return fail(error, QStringLiteral("Invalid or duplicate machine-set row"));
        const int count = members.toInt(-1);
        const int bootCount = boot.toInt(-1);
        if (count < 1 || count > 1024 || bootCount < 0 || bootCount > 64 ||
            members.toDouble() != count || boot.toDouble() != bootCount ||
            (status == QLatin1String("completed_btrfs_only") && bootCount != 0) ||
            (status == QLatin1String("completed_btrfs_and_boot_files") && bootCount == 0) ||
            item.value(QStringLiteral("bootable")).toBool(true))
            return fail(error, QStringLiteral("Machine-set counts or bootability invalid"));
        seen.insert(id);
        found.append({id,status,count,bootCount,complete});
    }
    *result = found;
    return true;
}
bool preview(const QByteArray &response, const QString &staging,
             RestorePreview *result, QString *error) {
    if (!result || !absoluteClean(staging) || staging == QLatin1String("/"))
        return fail(error, QStringLiteral("Invalid staging root"));
    QJsonDocument doc;
    if (!jsonDoc(response, &doc, error)) return false;
    if (!doc.isObject())
        return fail(error, QStringLiteral("Invalid restore preview structure"));
    const auto obj = doc.object();
    const auto plans = obj.value(QStringLiteral("plan"));
    const auto boots = obj.value(QStringLiteral("boot_plan"));
    if (obj.value(QStringLiteral("dry_run")).toBool(false) != true ||
        obj.value(QStringLiteral("bootable")).toBool(true) != false ||
        !plans.isArray() || !boots.isArray() ||
        plans.toArray().isEmpty() || plans.toArray().size() > 1024 ||
        boots.toArray().size() > 64)
        return fail(error, QStringLiteral("Invalid or unsafe machine restore plan"));
    QSet<QString> seenMounts;
    QStringList mounts;
    int i = 0;
    for (const auto &v : plans.toArray()) {
        if (!v.isObject())
            return fail(error, QStringLiteral("Non-object Btrfs plan entry"));
        const auto row = v.toObject();
        const auto mount = row.value(QStringLiteral("original_mount")).toString();
        const auto destination = row.value(QStringLiteral("staging")).toString();
        const auto archive = row.value(QStringLiteral("archive")).toString();
        const auto expected = QStringLiteral("%1/volume-%2")
            .arg(staging).arg(i, 3, 10, QLatin1Char('0'));
        if (!absoluteClean(mount) || !absoluteClean(destination) ||
            destination != expected || !archiveName(archive) || seenMounts.contains(mount))
            return fail(error, QStringLiteral("Invalid or duplicate Btrfs staging entry"));
        seenMounts.insert(mount);
        if (mounts.size() < 12) mounts.append(mount);
        ++i;
    }
    i = 0;
    for (const auto &v : boots.toArray()) {
        if (!v.isObject())
            return fail(error, QStringLiteral("Non-object boot-file plan entry"));
        const auto row = v.toObject();
        const auto mount = row.value(QStringLiteral("original_mount")).toString();
        const auto destination = row.value(QStringLiteral("staging")).toString();
        const auto archive = row.value(QStringLiteral("archive")).toString();
        static const QRegularExpression bootArchive(
            QStringLiteral("^[.]harbor-boot-[A-Za-z0-9_.-]{1,190}$"));
        const auto expected = QStringLiteral("%1/boot-files/boot-%2")
            .arg(staging).arg(i, 3, 10, QLatin1Char('0'));
        if (!absoluteClean(mount) || !absoluteClean(destination) ||
            destination != expected || !bootArchive.match(archive).hasMatch())
            return fail(error, QStringLiteral("Invalid boot-file staging entry"));
        ++i;
    }
    result->volumesCount = static_cast<int>(plans.toArray().size());
    result->mounts = mounts;
    result->bootFiles = static_cast<int>(boots.toArray().size());
    return true;
}
}
