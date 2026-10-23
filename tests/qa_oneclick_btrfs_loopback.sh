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
btrfs subvolume create "$work/mount/home" >/dev/null
printf 'first-machine-backup\n' > "$work/mount/source/qa.txt"
printf 'first-home-backup\n' > "$work/mount/home/home.txt"
# Store sealed archives on an INDEPENDENT filesystem, as in a real
# workstation -> NAS configuration. Btrfs synthetic per-subvolume st_dev
# differs from mountinfo in some kernels for directories inside nested
# source volumes; the mount guard correctly rejects such ambiguous roots.
mkdir "$work/repository"
export PYTHONPATH="$PWD/vendor/harbor-legacy"
repo="$work/repository"
profile="118e0b70-dced-4a95-9179-8b45efbd3f51"
backup() {
  python3 -m btrfs_backup_ng raw checkpoint-v2 set-backup \
    --target "$repo" --profile-id "$profile" \
    --source "$work/mount/source" --source "$work/mount/home" \
    --snapshot-provider harbor \
    --experimental --allow-local
}
backup > "$work/first.json"
python3 - "$work/first.json" <<'PY_ASSERT_FIRST'
import json,sys
messages=[json.loads(line) for line in open(sys.argv[1]) if line.strip().startswith("{")]
o=next(row for row in reversed(messages) if row.get("status","").startswith("completed_"))
assert o["status"] == "completed_btrfs_only", o
assert len(o["members"]) == 2, o
assert o["capture_completed_utc"],o
assert all(row.get("snapshot_created_utc") and row.get("snapshot_uuid")
           for row in o["members"]),o
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
printf 'second-home-backup\n' > "$work/mount/home/home.txt"
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
assert len(data["plan"])==2,data
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
assert any(x.read_bytes()==b"second-home-backup\n" for x in base.rglob("home.txt"))
PY_ASSERT_RESTORE
# Verify that the future restore can create NEW, inactive writable Btrfs
# subvolumes from the two received readonly archives, leaving the fresh
# source and the active root untouched. This is NOT a bootability certificate.
python3 - "$repo" "$setid" "$work/mount" "$work/mount/restore" <<'PY_INACTIVE'
import json
from pathlib import Path
import sys

from btrfs_backup_ng.core.cachyos_activation_plan import ActivationPlan
from btrfs_backup_ng.core.cachyos_inactive_subvolumes import prepare_inactive_subvolumes
from btrfs_backup_ng.core.rear_bridge_v2 import find_received_subvolume

repo, set_id, top, staging = map(Path, sys.argv[1:5])
set_uuid = str(set_id)
data = json.loads((repo / (".harbor-machine-set-" + set_uuid + ".json")).read_text())
assert len(data["members"]) == 2, data
mounts = {
    "/": "/@harbor-" + set_uuid[:8] + "-root",
    "/home": "/@harbor-" + set_uuid[:8] + "-home"
}
sources = {}
for i, member in enumerate(data["members"]):
    key = "/" if Path(member["original_mount"]).name == "source" else "/home"
    sources[key] = find_received_subvolume(
        staging / f"volume-{i:03d}", member["snapshot_uuid"])
plan = ActivationPlan(
    set_id=set_uuid, source_hostname="Pegasus", target_hostname="NewPegasus",
    fresh_machine_id="0" * 32, mounts=tuple(mounts.items()),
    fstab="", limine_cmdline="", bootloader="limine")
out = prepare_inactive_subvolumes(
    plan, sources, staging=staging, top_level=top)
assert (Path(out["/"]) / "qa.txt").read_bytes() == b"second-machine-backup\n"
assert (Path(out["/home"]) / "home.txt").read_bytes() == b"second-home-backup\n"
assert (top / "source/qa.txt").read_bytes() == b"second-machine-backup\n"
assert (top / "home/home.txt").read_bytes() == b"second-home-backup\n"
assert not (top / "@").exists()
print("PASS_REAL_BTRFS_INACTIVE_ALTERNATE_ROOT_PREPARED")
PY_INACTIVE
echo PASS_ONECLICK_REAL_BTRFS_TWO_DATED_SETS_AND_VERIFIED_RESTORE
