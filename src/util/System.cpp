#include "System.h"

#include <QFile>
#include <QProcess>
#include <QRegularExpression>
#include <QTextStream>
#include <unistd.h>

bool System::checkRootUid() { return geteuid() == 0; }

bool System::enableService(QString serviceName, bool enable)
{
    int exitCode;

    if (enable) {
        exitCode = System::runCmd("systemctl", {"enable", "--now", serviceName}, false).exitCode;
    } else {
        exitCode = System::runCmd("systemctl", {"disable", "--now", serviceName}, false).exitCode;
    }

    return exitCode == 0;
}

QStringList System::findEnabledUnits()
{

    static QRegularExpression qRegEx("[\t ]+");
    const QString bashOutput = System::runCmd("systemctl", {"list-unit-files", "--state=enabled", "-q", "--no-pager"}, false).output;
    const QStringList outputList = bashOutput.split('\n');
    QStringList serviceList;
    for (const QString &line : outputList) {
        serviceList.append(line.split(qRegEx).at(0));
    }

    return serviceList;
}

bool System::hasSystemd()
{
    // /proc/1/comm contains the command use to run the init system
    QFile file(QStringLiteral("/proc/1/comm"));
    if (!file.open(QIODevice::ReadOnly)) {
        return false;
    }

    if (file.readAll().trimmed() != "systemd") {
        return false;
    }

    return true;
}

bool System::isSubvolidInFstab()
{
    QFile file(QStringLiteral("/etc/fstab"));
    if (!file.open(QIODevice::ReadOnly)) {
        return false;
    }

    QTextStream fstabStream(&file);
    QString line;
    while (fstabStream.readLineInto(&line)) {
        if (!line.startsWith("#") && line.contains("subvolid")) {
            return true;
        }
    };

    return false;
}

Result System::runCmd(const QString &cmd, const QStringList &args, bool includeStderr, milliseconds timeout)
{
    QProcess proc;

    if (includeStderr)
        proc.setProcessChannelMode(QProcess::MergedChannels);

    proc.start(cmd, args);
    // Fail closed on failed spawn, timeout, or signal termination. The
    // previous implementation returned the exit code of an unfinished process,
    // which could incorrectly report success before a destructive action ends.
    if (!proc.waitForStarted(5000))
        return {-1, proc.errorString()};
    if (!proc.waitForFinished(static_cast<int>(timeout.count()))) {
        proc.kill();
        proc.waitForFinished(2000);
        return {-1, QStringLiteral("Command timed out: %1").arg(cmd)};
    }
    if (proc.exitStatus() != QProcess::NormalExit)
        return {-1, QStringLiteral("Command terminated abnormally: %1").arg(cmd)};
    return {proc.exitCode(), proc.readAllStandardOutput().trimmed()};
}

QString System::toHumanReadable(const uint64_t number)
{
    auto result = static_cast<double>(number);

    int i = 0;
    const QVector<QString> units = {"B", "kiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"};
    while (result > 1024) {
        result /= 1024;
        i++;
    }
    return QStringLiteral("%1 %2").arg(result, 0, 'f', 2).arg(units[i]);
}
