#pragma once
#include <QDateTime>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLocale>
#include <QString>
#include <QStringList>
#include <unistd.h>
namespace HarborProgress {
inline QString pick(const char *en, const char *fr, const char *zh) {
    const auto l = QLocale().language();
    return QString::fromUtf8(l == QLocale::French ? fr : l == QLocale::Chinese ? zh : en);
}
inline QJsonArray ownJobs() {
    bool ok = false;
    const auto origin = qEnvironmentVariable("PKEXEC_UID").toUInt(&ok);
    const auto uid = ok && origin > 0 ? origin : static_cast<uint>(getuid());
    QFile f(QStringLiteral("/run/btrfs-assistant-harbor/%1.json").arg(uid));
    if (!f.open(QFile::ReadOnly)) return {};
    const auto bytes = f.read(256 * 1024 + 1);
    if (bytes.size() > 256 * 1024) return {};
    const auto json = QJsonDocument::fromJson(bytes);
    if (!json.isObject() || json.object().value(QStringLiteral("version")).toInt() != 1) return {};
    const double updated = json.object().value(QStringLiteral("updated")).toDouble();
    if (updated <= 0 || QDateTime::currentSecsSinceEpoch() - updated > 30) return {};
    return json.object().value(QStringLiteral("jobs")).toArray();
}
inline QJsonObject active(const QString &id = {}) {
    QJsonObject newest;
    for (const auto &entry : ownJobs()) {
        const auto item = entry.toObject();
        if (item.value(QStringLiteral("state")).toString() != QLatin1String("running")) continue;
        if (!id.isEmpty() && item.value(QStringLiteral("id")).toString() != id) continue;
        if (newest.isEmpty() || item.value(QStringLiteral("started")).toDouble() >
                                  newest.value(QStringLiteral("started")).toDouble()) newest = item;
    }
    return newest;
}
inline QString size(double bytes) {
    return QString::number(bytes / 1073741824.0, 'f', 1) + QStringLiteral(" GiB");
}
inline QString duration(qint64 seconds) {
    if (seconds >= 86400) return QStringLiteral("%1d %2h").arg(seconds / 86400).arg(seconds % 86400 / 3600);
    if (seconds >= 3600) return QStringLiteral("%1h %2m").arg(seconds / 3600).arg(seconds % 3600 / 60);
    return QStringLiteral("%1 min").arg(qMax<qint64>(1, (seconds + 59) / 60));
}
inline QString overview(const QJsonObject &obj, bool tooltip = false) {
    if (obj.isEmpty()) return {};
    const double done = obj.value(QStringLiteral("bytes_read")).toDouble();
    const auto remaining = obj.value(QStringLiteral("stream_remaining_estimate"));
    const auto total = obj.value(QStringLiteral("stream_total_estimate"));
    const auto uploaded = obj.value(QStringLiteral("uploaded_bytes"));
    const auto networkLeft = obj.value(QStringLiteral("network_remaining_estimate"));
    const auto eta = obj.value(QStringLiteral("eta_seconds"));
    QStringList lines;
    lines << pick("Source stream", "Flux source", "源数据流")
              + QStringLiteral(": ") + size(done)
              + (total.isDouble() ? QStringLiteral(" / ~") + size(total.toDouble()) : QString());
    lines << (remaining.isDouble()
        ? pick("To analyze (estimated)", "Reste à analyser (estimé)", "预计剩余分析")
                  + QStringLiteral(": ~") + size(remaining.toDouble())
        : pick("Total stream: calculating", "Volume total : calcul en cours", "总量估算中"));
    if (uploaded.isDouble()) {
        lines << pick("New data sent", "Nouvelles données envoyées", "已发送新数据")
                  + QStringLiteral(": ") + size(uploaded.toDouble());
        if (networkLeft.isDouble())
            lines << pick("Still to send (estimated)", "Reste à envoyer (estimé)", "预计剩余发送")
                      + QStringLiteral(": ~") + size(networkLeft.toDouble());
    } else {
        const auto observed = obj.value(QStringLiteral("nfs_observed_bytes"));
        if (observed.isDouble()) {
            lines << pick("NFS writes since tracking began (shared)",
                          "Écritures NFS depuis le suivi (montage partagé)",
                          "监测开始后的 NFS 写入（共享挂载）")
                  + QStringLiteral(": ~") + size(observed.toDouble());
            if (networkLeft.isDouble())
                lines << pick("Still to send (rough estimate)", "Reste à envoyer (très approximatif)",
                              "预计剩余发送（粗略）") + QStringLiteral(": ~") + size(networkLeft.toDouble());
        } else {
            lines << pick("Sent data: sampling...", "Go envoyés : échantillonnage...",
                          "发送数据采样中...");
        }
    }
    lines << (eta.isDouble()
        ? pick("ETA (estimated)", "Temps restant (estimé)", "预计剩余时间")
                   + QStringLiteral(": ~") + duration(static_cast<qint64>(eta.toDouble()))
        : pick("ETA: calculating", "Temps restant : calcul en cours", "预计时间计算中"));
    return lines.join(tooltip ? QStringLiteral("\n") : QStringLiteral("  |  "));
}
}
