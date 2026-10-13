#include "util/MachineSetProtocol.h"
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonValue>
#include <QtGlobal>
#define CHECK(expr) do { if (!(expr)) qFatal("Failed: %s", #expr); } while (false)

static QByteArray encoded(const QJsonValue &value) {
    if (value.isArray()) return QJsonDocument(value.toArray()).toJson(QJsonDocument::Compact);
    return QJsonDocument(value.toObject()).toJson(QJsonDocument::Compact);
}

int main() {
    using namespace HarborMachineProtocol;
    const QString id("a5d970db-9664-4be8-a0fb-bb1e93c60ec3");
    const QJsonObject row{{"set_id",id},{"status","completed_btrfs_and_boot_files"},
                          {"members",2},{"boot_partitions",1},{"bootable",false}};
    QList<BackupSet> records;
    QString error;
    const auto good = encoded(QJsonArray{row});
    CHECK(catalog(good, &records, &error));
    CHECK(records.size() == 1 && records[0].volumes == 2 && records[0].bootFiles == 1);
    CHECK(catalog("[]", &records, &error) && records.isEmpty());
    CHECK(!catalog(encoded(QJsonArray{row,row}), &records, &error));
    CHECK(!catalog("[{}]", &records, &error));
    CHECK(!catalog("{", &records, &error));
    QJsonObject bad = row;
    bad.insert("bootable", true);
    CHECK(!catalog(encoded(QJsonArray{bad}), &records, &error));
    bad = row; bad.insert("status", "pending");
    CHECK(catalog(encoded(QJsonArray{bad}), &records, &error));
    CHECK(records.size() == 1 && !records[0].complete);
    bad = row; bad.insert("status", "completed_but_fake");
    CHECK(catalog(encoded(QJsonArray{bad}), &records, &error));
    CHECK(records.size() == 1 && !records[0].complete);
    bad = row; bad.insert("status", "../malicious");
    CHECK(!catalog(encoded(QJsonArray{bad}), &records, &error));
    bad = row; bad.insert("status", "completed_btrfs_only");
    CHECK(!catalog(encoded(QJsonArray{bad}), &records, &error));
    bad = row; bad.insert("members", 1.5);
    CHECK(!catalog(encoded(QJsonArray{bad}), &records, &error));
    bad = row; bad.insert("set_id", "../etc");
    CHECK(!catalog(encoded(QJsonArray{bad}), &records, &error));
    CHECK(!catalog(QByteArray(1048577, 'x'), &records, &error));
    QJsonObject v0{{"archive","machine-000"},{"original_mount","/"},
                   {"staging","/mnt/staging/volume-000"}};
    QJsonObject v1{{"archive","machine-001"},{"original_mount","/home"},
                   {"staging","/mnt/staging/volume-001"}};
    const QJsonObject boot{{"archive",".harbor-boot-qa.tar.gz"},
                           {"original_mount","/boot/efi"},
                           {"staging","/mnt/staging/boot-files/boot-000"}};
    QJsonObject doc{{"dry_run",true},{"bootable",false},
                    {"plan",QJsonArray{v0,v1}},{"boot_plan",QJsonArray{boot}}};
    RestorePreview result;
    CHECK(preview(encoded(doc), "/mnt/staging", &result, &error));
    CHECK(result.volumesCount == 2 && result.bootFiles == 1 && result.mounts.size() == 2);
    CHECK(!preview(encoded(doc), "/", &result, &error));
    CHECK(!preview(encoded(doc), "/mnt/staging/../staging", &result, &error));
    bad = doc; bad.insert("bootable", true);
    CHECK(!preview(encoded(bad), "/mnt/staging", &result, &error));
    bad = doc; bad.insert("dry_run", false);
    CHECK(!preview(encoded(bad), "/mnt/staging", &result, &error));
    bad = doc; bad.insert("plan", QJsonArray{});
    CHECK(!preview(encoded(bad), "/mnt/staging", &result, &error));
    QJsonObject wrong = v1;
    wrong.insert("original_mount","/");
    bad = doc; bad.insert("plan",QJsonArray{v0,wrong});
    CHECK(!preview(encoded(bad), "/mnt/staging", &result, &error));
    wrong = v1; wrong.insert("staging","/mnt/staging/volume-001/../other");
    bad = doc; bad.insert("plan",QJsonArray{v0,wrong});
    CHECK(!preview(encoded(bad), "/mnt/staging", &result, &error));
    wrong = v0; wrong.insert("archive","../unsafe");
    bad = doc; bad.insert("plan",QJsonArray{wrong});
    CHECK(!preview(encoded(bad), "/mnt/staging", &result, &error));
    wrong = boot; wrong.insert("staging","/mnt/staging/boot-files/../escape");
    bad = doc; bad.insert("boot_plan",QJsonArray{wrong});
    CHECK(!preview(encoded(bad), "/mnt/staging", &result, &error));
    wrong = boot; wrong.insert("archive","../../etc/shadow");
    bad = doc; bad.insert("boot_plan",QJsonArray{wrong});
    CHECK(!preview(encoded(bad), "/mnt/staging", &result, &error));
    return 0;
}
