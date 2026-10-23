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
    // Refuse overwriting any prior staged recovery. A failed attempt needs
    // explicit cleanup or an independent new backup set.
    int reader = dup(fd);
    if (reader < 0) return fail(QStringLiteral("Cannot read staging directory"));
    DIR *dir = fdopendir(reader);
    if (!dir) { close(reader); return fail(QStringLiteral("Cannot inspect staging")); }
    bool empty = true;
    while (auto *entry = readdir(dir)) {
        if (std::strcmp(entry->d_name, ".") != 0 &&
            std::strcmp(entry->d_name, "..") != 0) {
            empty = false;
            break;
        }
    }
    closedir(dir);
    if (!empty) return fail(QStringLiteral("Recovery directory is not empty"));
    close(fd);
    *staging = QStringLiteral("/var/lib/btrfs-assistant-harbor/recovery/set-") + setId;
    return true;
}
}
