#!/usr/bin/env bash
# Disposable real Btrfs one-click checkpoint-v2 backup and staged recovery.
# Explicit fixture --source: no CI host root or EFI is captured.
set -euo pipefail
test "$(id -u)" -eq 0 || { echo "root only on disposable CI"; exit 51; }
test "$GITHUB_ACTIONS" = "true" || { echo "Disposable CI runner only"; exit 52; }
test -f vendor/harbor-legacy/btrfs_backup_ng/__main__.py
work="$(mktemp -d /tmp/harbor-oneclick-loop-XXXXXX)"
mounted=0
cleanup() {
  if ((mounted)); then umount "$work/mount" >/dev/null 2>&1 || true; fi
  rm -rf "$work"
}
trap cleanup EXIT
truncate -s 1200M "$work/fixture.img"
mkfs.btrfs -fq "$work/fixture.img"
mkdir "$work/mount"
mount -o loop -t btrfs "$work/fixture.img" "$work/mount"
mounted=1
btrfs subvolume create "$work/mount/source" >/dev/null
printf 'first-machine-backup\n' > "$work/mount/source/qa.txt"
mkdir "$work/mount/repository"
export PYTHONPATH="$PWD/vendor/harbor-legacy"
repo="$work/mount/repository"
profile="118e0b70-dced-4a95-9179-8b45efbd3f51"
backup() {
  python3 -m btrfs_backup_ng raw checkpoint-v2 set-backup \
    --target "$repo" --profile-id "$profile" \
    --source "$work/mount/source" --snapshot-provider harbor \
    --experimental --allow-local
}
backup > "$work/first.json"
python3 - "$work/first.json" <<'PY_ASSERT_FIRST'
import json,sys
messages=[json.loads(line) for line in open(sys.argv[1]) if line.strip().startswith("{")]
o=next(row for row in reversed(messages) if row.get("status","").startswith("completed_"))
assert o["status"] == "completed_btrfs_only", o
assert len(o["members"]) == 1, o
PY_ASSERT_FIRST
python3 -m btrfs_backup_ng raw checkpoint-v2 set-list \
  --target "$repo" > "$work/one.json"
python3 - "$work/one.json" <<'PY_ASSERT_CATALOG'
import json,sys,socket
rows=json.load(open(sys.argv[1]))
assert len(rows)==1,rows
assert rows[0]["machine_name"]==socket.gethostname(),rows
assert rows[0]["bootable"] is False,rows
PY_ASSERT_CATALOG
printf 'second-machine-backup\n' > "$work/mount/source/qa.txt"
backup > "$work/second.json"
python3 -m btrfs_backup_ng raw checkpoint-v2 set-list \
  --target "$repo" > "$work/two.json"
setid="$(python3 - "$work/two.json" <<'PY_FIND_SET'
import json,sys
rows=json.load(open(sys.argv[1]))
assert len(rows)==2,rows
assert all(x["status"]=="completed_btrfs_only" for x in rows),rows
ids=[x["set_id"] for x in rows]
assert len(set(ids))==2,rows
print(max(rows, key=lambda x: x["created_utc"])["set_id"])
PY_FIND_SET
)"
mkdir "$work/mount/restore"
python3 -m btrfs_backup_ng raw checkpoint-v2 set-restore \
  --target "$repo" --set-id "$setid" \
  --staging "$work/mount/restore" --experimental --allow-local \
  > "$work/preview.json"
python3 - "$work/preview.json" <<'PY_ASSERT_PREVIEW'
import json,sys
data=json.load(open(sys.argv[1]))
assert data["dry_run"] is True and data["bootable"] is False,data
assert len(data["plan"])==1,data
PY_ASSERT_PREVIEW
python3 -m btrfs_backup_ng raw checkpoint-v2 set-restore \
  --target "$repo" --set-id "$setid" \
  --staging "$work/mount/restore" --experimental --allow-local --confirm \
  > "$work/restored.json"
python3 - "$work/restored.json" "$work/mount/restore" <<'PY_ASSERT_RESTORE'
import json,sys,pathlib
obj=json.load(open(sys.argv[1]))
assert obj["restored"] is True and obj["bootable"] is False,obj
base=pathlib.Path(sys.argv[2])
assert any(x.read_bytes()==b"second-machine-backup\n" for x in base.rglob("qa.txt"))
PY_ASSERT_RESTORE
echo PASS_ONECLICK_REAL_BTRFS_TWO_DATED_SETS_AND_VERIFIED_RESTORE
