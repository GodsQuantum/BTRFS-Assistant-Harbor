#!/usr/bin/env bash
# Native Snapper parity gate on a disposable Btrfs loop image. No host snapshots.
set -euo pipefail
test "$(id -u)" -eq 0 || { echo "Must run in isolated root-owned CI fixture"; exit 51; }
work="$(mktemp -d /tmp/harbor-snapper-native-XXXXXX)"
config="harborqa$$"
mounted=0
configured=0
cleanup() {
  if ((configured)); then snapper --no-dbus -c "$config" delete-config >/dev/null 2>&1 || true; fi
  if ((mounted)); then
    btrfs subvolume delete "$work/mount/source" >/dev/null 2>&1 || true
    umount "$work/mount" >/dev/null 2>&1 || true
  fi
  rm -rf "$work"
}
trap cleanup EXIT
truncate -s 1536M "$work/fixture.img"
mkfs.btrfs -fq "$work/fixture.img"
mkdir "$work/mount"
mount -o loop -t btrfs "$work/fixture.img" "$work/mount"
mounted=1
btrfs subvolume create "$work/mount/source" >/dev/null
printf 'initial\n' > "$work/mount/source/qa.txt"
snapper --no-dbus -c "$config" create-config "$work/mount/source"
configured=1
first="$(snapper --no-dbus -c "$config" create --read-only --print-number -d 'Harbor QA before')"
test "$first" -gt 0
printf 'updated\n' > "$work/mount/source/qa.txt"
second="$(snapper --no-dbus -c "$config" create --read-only --print-number -d 'Harbor QA after')"
test "$second" -gt "$first"
test "$(cat "$work/mount/source/.snapshots/$first/snapshot/qa.txt")" = "initial"
test "$(cat "$work/mount/source/.snapshots/$second/snapshot/qa.txt")" = "updated"
btrfs property get -ts "$work/mount/source/.snapshots/$first/snapshot" ro | grep -q 'ro=true'
btrfs property get -ts "$work/mount/source/.snapshots/$second/snapshot" ro | grep -q 'ro=true'
snapper --no-dbus -c "$config" list --disable-used-space > "$work/list.txt"
grep -q 'Harbor QA before' "$work/list.txt"
grep -q 'Harbor QA after' "$work/list.txt"
snapper --no-dbus -c "$config" status "$first..$second" > "$work/status.txt"
grep -q qa.txt "$work/status.txt"
if [[ -n "${HARBOR_GUI_QA_SNAPPER_TEST:-}" ]]; then
  test -x "$HARBOR_GUI_QA_SNAPPER_TEST"
  QT_QPA_PLATFORM=offscreen HARBOR_GUI_QA_SNAPPER_CONFIG="$config" \
    "$HARBOR_GUI_QA_SNAPPER_TEST" realSnapperSnapshotsAppearInRemoteBackupUi
fi
snapper --no-dbus -c "$config" delete --sync "$first" "$second"
test ! -d "$work/mount/source/.snapshots/$first/snapshot"
test ! -d "$work/mount/source/.snapshots/$second/snapshot"
echo "PASS_SNAPSHOT_NATIVE_CREATE_LIST_DIFF_READ_ONLY_DELETE"
