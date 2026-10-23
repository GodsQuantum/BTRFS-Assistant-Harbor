#pragma once
// Creates a root-owned, empty staging directory on the running CachyOS
// Btrfs volume. Only creates directories; never formats a disk, changes
// mounts, replaces an existing file, or activates a received subvolume.
#include <QString>
#include <QRegularExpression>
#include <cerrno>
#include <cstring>
#include <fcntl.h>
#include <dirent.h>
#include <QStringList>
#include <QUuid>
#include <sys/stat.h>
#include <sys/statfs.h>
#include <unistd.h>
#ifdef __linux__
#include <linux/magic.h>
#endif

namespace HarborStaging {
inline bool prepare(const QString &setId, QString *staging, QString *error) {
    static const QRegularExpression uuid(
        QStringLiteral("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"));
    if (!uuid.match(setId).hasMatch() || !staging) {
        if (error) *error = QStringLiteral("Unsafe backup identity");
        return false;
    }
    if (geteuid() != 0) {
        if (error) *error = QStringLiteral("Recovery preparation requires privileged Harbor");
        return false;
    }
    // System-controlled paths, never repository-provided path components.
    const QStringList children{
        QStringLiteral("btrfs-assistant-harbor"),
        QStringLiteral("recovery"),
        QStringLiteral("set-") + setId
    };
    int fd = open("/var/lib", O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    if (fd < 0) {
        if (error) *error = QStringLiteral("Cannot open /var/lib");
        return false;
    }
    auto fail = [&](const QString &message) {
        if (error) *error = message;
        close(fd);
        return false;
    };
    for (const auto &part : children) {
        const auto name = part.toUtf8();
        if (mkdirat(fd, name.constData(), 0700) != 0 && errno != EEXIST)
            return fail(QStringLiteral("Cannot prepare recovery folder"));
        const int child = openat(fd, name.constData(),
                                 O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
        if (child < 0) return fail(QStringLiteral("Recovery folder is not a real directory"));
        struct stat state {};
        if (fstat(child, &state) != 0 || state.st_uid != 0 ||
            (state.st_mode & 0022) != 0 || !S_ISDIR(state.st_mode)) {
            close(child);
            return fail(QStringLiteral("Recovery folder has unsafe permissions"));
        }
        close(fd);
        fd = child;
    }
    // A disk install created on ext4 cannot receive Btrfs snapshots.
    struct statfs fs {};
    if (fstatfs(fd, &fs) != 0 || fs.f_type != BTRFS_SUPER_MAGIC)
        return fail(QStringLiteral("New CachyOS installation must use Btrfs"));
    // A failed receive must not force a normal user to delete root-owned
    // staging files from a terminal. Create a distinct, empty attempt for
    // every click, preserving old incomplete attempts for later diagnosis.
    // Bound retained attempts to avoid silently consuming the entire disk.
    int reader = dup(fd);
    if (reader < 0) return fail(QStringLiteral("Cannot inspect staging directory"));
    DIR *dir = fdopendir(reader);
    if (!dir) { close(reader); return fail(QStringLiteral("Cannot inspect staging")); }
    int attempts = 0;
    while (auto *entry = readdir(dir)) {
        if (std::strncmp(entry->d_name, "attempt-", 8) == 0) ++attempts;
    }
    closedir(dir);
    if (attempts >= 16) return fail(QStringLiteral(
        "Too many retained recovery attempts: deliberate cleanup required"));
    const auto id = QUuid::createUuid().toString(QUuid::WithoutBraces);
    const auto name = (QStringLiteral("attempt-") + id).toUtf8();
    if (mkdirat(fd, name.constData(), 0700) != 0)
        return fail(QStringLiteral("Cannot allocate unique recovery attempt"));
    const int attempt = openat(fd, name.constData(),
                               O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    if (attempt < 0) return fail(QStringLiteral("Cannot inspect allocated recovery attempt"));
    struct stat state {};
    const bool valid = fstat(attempt, &state) == 0 && S_ISDIR(state.st_mode) &&
                       state.st_uid == 0 && (state.st_mode & 0077) == 0;
    close(attempt);
    if (!valid) return fail(QStringLiteral("Recovery attempt has unsafe permissions"));
    close(fd);
    *staging = QStringLiteral("/var/lib/btrfs-assistant-harbor/recovery/set-")
               + setId + QLatin1Char('/') + QString::fromUtf8(name);
    return true;
}
}
