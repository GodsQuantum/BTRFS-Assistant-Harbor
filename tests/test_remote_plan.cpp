#include "util/RemoteBackupPlan.h"
#include <QDebug>
#define REQUIRE(condition) do { if (!(condition)) qFatal("Check failed: %s", #condition); } while (false)
#include <QStringList>
#include <QUuid>
int main() {
  using namespace HarborRemote;
  const QString id = profileId("root", "/mnt/backup");
  REQUIRE(!QUuid(id).isNull());
  REQUIRE(id == "3554efe8-75e3-59bd-97a3-0526b0fd90e2");
  REQUIRE(id == profileId("root", "/mnt/backup"));
  REQUIRE(id != profileId("home", "/mnt/backup"));
  REQUIRE(archiveName("root", 123) == "snap-root-123");
  REQUIRE(archiveName("root/unsafe", 123).isEmpty());
  const QStringList send = sendArguments("root", 123, "/mnt/backup", false);
  REQUIRE(send.contains("selected-snapper"));
  REQUIRE(send.contains("--experimental"));
  REQUIRE(send.contains("--snapper-number"));
  REQUIRE(send.contains("123"));
  REQUIRE(!send.contains("--allow-local"));
  REQUIRE(sendArguments("root", 123, "/non-existing/../../etc", false).isEmpty());
  REQUIRE(sendArguments("root", 0, "/mnt/backup", false).isEmpty());
  REQUIRE(sendArguments("root", 123, "relative", false).isEmpty());
  REQUIRE(sendArguments("root", 123, "/mnt/backup", true).contains("--allow-local"));
  const QStringList schedule = scheduleArguments("root", "/mnt/backup", false);
  REQUIRE(schedule.contains("schedule-run"));
  REQUIRE(schedule.contains("--name-prefix"));
  REQUIRE(schedule.contains(profileId("root", "/mnt/backup")));
  const QStringList restore = previewRestoreArguments("/mnt/backup", "snap-root-123", "/mnt/staging");
  REQUIRE(restore.contains("--dry-run"));
  REQUIRE(restore.contains("raw:///mnt/backup"));
  REQUIRE(previewRestoreArguments("/mnt/backup", "../invalid", "/mnt/staging").isEmpty());
  REQUIRE(previewRestoreArguments("/mnt/backup", "snap-root-123", "/").isEmpty());
  const QStringList verify = verifyArguments("/mnt/backup", "snap-root-123");
  REQUIRE(verify.contains("--json"));
  REQUIRE(verify.contains("--snapshot"));
  return 0;
}
