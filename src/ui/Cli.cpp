#include "Cli.h"
#include "util/System.h"

static void displayError(const QString &error) { QTextStream(stderr) << "Error: " << error << Qt::endl; }

static QStringList getSnapperSnapshotList(Snapper *snapper)
{
    QStringList targets = snapper->subvolKeys();
    QStringList output;
    targets.sort();
    for (const QString &target : std::as_const(targets)) {
        QList<SnapperSubvolume> subvols = snapper->subvols(target);
        std::sort(subvols.begin(), subvols.end(),
                  [](const SnapperSubvolume &a, const SnapperSubvolume &b) { return a.snapshotNum < b.snapshotNum; });
        for (const SnapperSubvolume &subvol : std::as_const(subvols)) {
            output.append(target + "\t" + QString::number(subvol.snapshotNum) + "\t" + subvol.time.toString() + "\t" + subvol.type + "\t" +
                          subvol.subvol + "\t" + subvol.uuid);
        }
    }
    return output;
}

Cli::Cli(QObject *parent) : QObject{parent} {}

int Cli::listSnapshots(Snapper *snapper)
{
    // Ensure the application is running as root
    if (!System::checkRootUid()) {
        displayError(tr("You must run this application as root"));
        return 1;
    }

    const QStringList snapshotInfoList = getSnapperSnapshotList(snapper);

    int index = 0;
    for (const QString &snapshotInfo : snapshotInfoList) {
        QTextStream(stdout) << ++index << "\t" << snapshotInfo << Qt::endl;
    }

    return 0;
}

int Cli::restore(Btrfs *btrfs, Snapper *snapper, const int index)
{
    // Ensure the application is running as root
    if (!System::checkRootUid()) {
        displayError(tr("You must run this application as root"));
        return 1;
    }

    const QStringList snapshotInfoList = getSnapperSnapshotList(snapper);

    const QStringList selectedSnapshot = snapshotInfoList[index - 1].split("\t");

    if (selectedSnapshot.count() != 6) {
        displayError(tr("Failed to parse snapshot list"));
        return 1;
    }

    const QString subvolume = selectedSnapshot.at(4);
    const QString uuid = selectedSnapshot.at(5);

    if (!Btrfs::isSnapper(subvolume)) {
        displayError(tr("This is not a snapshot that can be restored by this application"));
        return 1;
    }

    // Ensure the list of subvolumes is not out-of-date
    btrfs->loadSubvols(uuid);

    const uint64_t subvolId = btrfs->subvolId(uuid, subvolume);
    if (subvolId == 0) {
        displayError(tr("Source snapshot not found"));
    }

    const SubvolResult subvolResultSnapshot = Snapper::findSnapshotSubvolume(subvolume);
    if (!subvolResultSnapshot.success) {
        displayError(tr("Snapshot subvolume not found"));
        return 1;
    }

    // Check the map for the target subvolume
    const SubvolResult sr = snapper->findTargetSubvol(subvolResultSnapshot.name, uuid);
    const uint64_t targetId = btrfs->subvolId(uuid, sr.name);

    if (targetId == 0 || !sr.success) {
        displayError(tr("Target not found"));
        return 1;
    }

    QTextStream(stdout) << tr(QString("Restoring snapshot %1").arg(subvolume).toUtf8()) << Qt::endl;

    // Everything checks out, time to do the restore
    RestoreResult restoreResult = btrfs->restoreSubvol(uuid, subvolId, targetId);

    // Report the outcome to the end user
    if (restoreResult.isSuccess) {
        QTextStream(stdout) << tr("Snapshot restoration complete.") << Qt::endl
                            << tr("A copy of the original subvolume has been saved as ") << restoreResult.backupSubvolName << Qt::endl
                            << tr("Please reboot immediately\n");
        return 0;
    } else {
        displayError(restoreResult.failureMessage);
        return 1;
    }
}
