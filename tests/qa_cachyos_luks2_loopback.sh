#!/usr/bin/env bash
# Real LUKS2+Argon2id+Btrfs on an isolated GitHub disposable image only.
set -euo pipefail
[[ "$GITHUB_ACTIONS" == true && "$(id -u)" -eq 0 ]] || exit 61
work="$(mktemp -d /tmp/harbor-luks-XXXXXXXX)"
mapper="harbor-qa-$RANDOM-$RANDOM"
mounted=0
opened=0
esp_mounted=0
cleanup() {
  if ((esp_mounted)); then umount "$work/esp" || true; fi
  if ((mounted)); then umount "$work/top" || true; fi
  if ((opened)); then cryptsetup close "$mapper" || true; fi
  if ! mountpoint -q "$work/top" && ! cryptsetup status "$mapper" >/dev/null 2>&1; then
    rm -rf -- "$work"
  fi
}
trap cleanup EXIT
truncate -s 1200M "$work/disk.img"
head -c 32 /dev/urandom > "$work/keyfile"
chmod 0600 "$work/keyfile"
cryptsetup luksFormat "$work/disk.img" --type luks2 --batch-mode \
  --pbkdf argon2id --pbkdf-memory 16384 --pbkdf-parallel 1 --iter-time 100 \
  --key-file "$work/keyfile" >/dev/null
luks_uuid="$(cryptsetup luksUUID "$work/disk.img")"
header_sha="$(dd if="$work/disk.img" bs=1M count=16 status=none | sha256sum | cut -d' ' -f1)"
cryptsetup open "$work/disk.img" "$mapper" --key-file "$work/keyfile"
opened=1
mkfs.btrfs -qf "/dev/mapper/$mapper"
mkdir "$work/top"
mount -t btrfs -o subvolid=5 "/dev/mapper/$mapper" "$work/top"
mounted=1
btrfs subvolume create "$work/top/@" >/dev/null
btrfs subvolume create "$work/top/@home" >/dev/null
mkdir -p "$work/top/@/etc/default"
printf 'Pegasus-root\n' > "$work/top/@/qa.txt"
printf 'Pegasus-home\n' > "$work/top/@home/home.txt"
printf 'Pegasus\n' > "$work/top/@/etc/hostname"
printf 'ffffffffffffffffffffffffffffffff\n' > "$work/top/@/etc/machine-id"
printf 'ID=cachyos\n' > "$work/top/@/etc/os-release"
printf 'UUID=11111111-1111-4111-8111-111111111111 / btrfs defaults,subvol=/@ 0 0\n' > "$work/top/@/etc/fstab"
printf 'KERNEL_CMDLINE[default]+="rw rootflags=subvol=/@"\n' > "$work/top/@/etc/default/limine"
# Separate FAT32/ESP loopback, never the CI runner's /boot.
truncate -s 128M "$work/esp.img"
mkfs.vfat -F 32 -I "$work/esp.img" >/dev/null
mkdir "$work/esp"
mount -t vfat -o loop "$work/esp.img" "$work/esp"
esp_mounted=1
printf 'dummy-cachyos-kernel\n' > "$work/esp/vmlinuz-linux-cachyos"
printf 'dummy-cachyos-initramfs\n' > "$work/esp/initramfs-linux-cachyos.img"
cat > "$work/esp/limine.conf" <<'NATIVE_LIMINE'
timeout: 5
default_entry: 2

/+CachyOS
  //linux-cachyos
  comment: Kernel version: 7.3.0-3-cachyos
  protocol: linux
  path: boot():/vmlinuz-linux-cachyos
  module_path: boot():/initramfs-linux-cachyos.img
  cmdline: quiet rw rootflags=subvol=/@ rd.luks.uuid=33333333-3333-4333-8333-333333333333
NATIVE_LIMINE
mkdir "$work/repo" "$work/top/receive"
export PYTHONPATH="$PWD/vendor/harbor-legacy"
python3 -m btrfs_backup_ng raw checkpoint-v2 set-backup \
  --target "$work/repo" --profile-id 118e0b70-dced-4a95-9179-8b45efbd3f51 \
  --source "$work/top/@" --source "$work/top/@home" \
  --snapshot-provider harbor --experimental --allow-local > "$work/backup.jsonl"
python3 -m btrfs_backup_ng raw checkpoint-v2 set-list --target "$work/repo" > "$work/catalog.json"
setid="$(python3 - "$work/catalog.json" <<'PY_SET'
import json,sys
data=json.load(open(sys.argv[1]))
assert len(data)==1 and data[0]["status"]=="completed_btrfs_only",data
print(data[0]["set_id"])
PY_SET
)"
python3 -m btrfs_backup_ng raw checkpoint-v2 set-restore \
  --target "$work/repo" --set-id "$setid" --staging "$work/top/receive" \
  --experimental --allow-local --confirm > "$work/received.json"
python3 - "$work/repo" "$setid" "$work/top" "$work/top/receive" "$luks_uuid" "$work/esp" <<'PY_CERT'
import json,sys
from pathlib import Path
from btrfs_backup_ng.core.rear_bridge_v2 import find_received_subvolume
from btrfs_backup_ng.core.cachyos_activation_plan import ActivationPlan
from btrfs_backup_ng.core.cachyos_inactive_subvolumes import prepare_inactive_subvolumes
from btrfs_backup_ng.core.cachyos_inactive_config import configure_inactive_root
from btrfs_backup_ng.core.cachyos_limine_recovery_entry import preview_recovery_menu
from btrfs_backup_ng.core.cachyos_offline_esp import stage_additive_limine_entry
repo, sid, top, staging = map(Path, sys.argv[1:5])
esp=Path(sys.argv[6])
sid=str(sid)
luks=sys.argv[5]
data=json.loads((repo/(".harbor-machine-set-"+sid+".json")).read_text())
assert len(data["members"])==2
received={}
for i,m in enumerate(data["members"]):
    key="/" if Path(m["original_mount"]).name=="@" else "/home"
    received[key]=find_received_subvolume(staging/f"volume-{i:03d}",
                                          m["snapshot_uuid"])
subvols={"/":"/@harbor-"+sid[:8]+"-root","/home":"/@harbor-"+sid[:8]+"-home"}
cmd=("rw rootflags=subvol="+subvols["/"]+
     " rd.luks.uuid="+luks+" root=/dev/mapper/luks-"+luks)
plan=ActivationPlan(
    set_id=sid,source_hostname="Pegasus",target_hostname="NewPegasus",
    fresh_machine_id="0"*32,mounts=tuple(subvols.items()),
    fstab=("UUID=22222222-2222-4222-8222-222222222222 / btrfs "
           "defaults,subvol="+subvols["/"]+" 0 0\n"),
    limine_cmdline=cmd,bootloader="limine",
)
created=prepare_inactive_subvolumes(plan,received,staging=staging,top_level=top)
report=configure_inactive_root(
    plan,Path(created["/"]),fresh_crypttab="",
    fresh_limine_config=('KERNEL_CMDLINE[default]+="rw rootflags=subvol=/@ '
                         'rd.luks.uuid='+luks+'"\n'),
)
assert report["bootable_certified"] is False
assert report["bootloader_invoked"] is False
assert (Path(created["/"])/"qa.txt").read_bytes()==b"Pegasus-root\n"
assert (Path(created["/home"])/"home.txt").read_bytes()==b"Pegasus-home\n"
assert (Path(created["/"])/"etc/hostname").read_text()=="NewPegasus\n"
assert (Path(created["/"])/"etc/machine-id").read_text()=="0"*32+"\n"
assert luks in (Path(created["/"])/"etc/default/limine").read_text()
assert (top/"@/etc/hostname").read_text()=="Pegasus\n"
assert (top/"@/qa.txt").read_bytes()==b"Pegasus-root\n"
assert (top/"@home/home.txt").read_bytes()==b"Pegasus-home\n"
original=(esp/"limine.conf").read_text()
preview=preview_recovery_menu(
    original,plan,restored_module_versions={"7.3.0-3-cachyos"},
    secure_boot_state="disabled",
)
stage=stage_additive_limine_entry(
    esp,preview,set_id=sid,secure_boot_state="disabled",
)
assert not stage["bootable_certified"]
assert not stage["reboot_performed"]
assert stage["default_selection_preserved"]
assert Path(stage["backup_file"]).read_text()==original
new_config=(esp/"limine.conf").read_text()
assert new_config.startswith(original)
assert preview.menu_addition in new_config
assert new_config.count("default_entry: 2")==1
assert luks in new_config
assert (top/"@/etc/hostname").read_text()=="Pegasus\n"
print("PASS_REAL_FAT32_LIMINE_ADDITIVE_RECOVERY_WITH_FALLBACK")
print("PASS_NATIVE_LUKS2_ENCRYPTED_BTRFS_TRANSFER_AND_INACTIVE_ROOT")
PY_CERT
[[ "$(cryptsetup luksUUID "$work/disk.img")" == "$luks_uuid" ]]
new_sha="$(dd if="$work/disk.img" bs=1M count=16 status=none | sha256sum | cut -d' ' -f1)"
[[ "$new_sha" == "$header_sha" ]] || { echo LUKS2_HEADER_MODIFIED; exit 65; }
echo PASS_LUKS2_FRESH_HEADER_UNCHANGED
