#pragma once
#include <QByteArray>
#include <QList>
#include <QString>
#include <QStringList>
namespace HarborMachineProtocol {
struct BackupSet {
    QString id;
    QString status;
    int volumes = 0;
    int bootFiles = 0;
};
struct RestorePreview {
    int volumesCount = 0;
    QStringList mounts;
    int bootFiles = 0;
};
bool catalog(const QByteArray &response, QList<BackupSet> *result, QString *error);
bool preview(const QByteArray &response, const QString &staging,
             RestorePreview *result, QString *error);
}
