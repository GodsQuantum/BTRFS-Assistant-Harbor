#!/usr/bin/env bash
# Native CachyOS rootfs -> encrypted restored Btrfs root -> UEFI Limine.
# Runs ONLY on the disposable GitHub Actions runner.
set -euo pipefail
test "$GITHUB_ACTIONS" = true
test "$(id -u)" -eq 0
iso="$1"
work="$(mktemp -d /tmp/harbor-cachyos-uefi-XXXXXXXX)"
loop=""
mapper=""
cleanup() {
  set +eu
  if test -f "$work/serial.log"; then
    cp "$work/serial.log" /tmp/harbor-uefi-lab/guest-serial.log || true
  fi
  if test -f "$work/mkinitcpio.log"; then
    cp "$work/mkinitcpio.log" /tmp/harbor-uefi-lab/mkinitcpio.log || true
  fi
  for dir in dev/pts dev proc sys run boot; do
    mountpoint -q "$work/root/$dir" && umount -l "$work/root/$dir"
  done
  mountpoint -q "$work/root" && umount -l "$work/root"
  mountpoint -q "$work/top" && umount -l "$work/top"
  test -z "$mapper" || cryptsetup close "$mapper"
  test -z "$loop" || losetup -d "$loop"
  test "$HARBOR_KEEP_FAILED_LAB" = 1 || rm -rf -- "$work"
}
trap cleanup EXIT
echo "HARBOR_UEFI_TEST_LAB=$work"
truncate -s 22G "$work/disk.raw"
sgdisk --clear --new=1:2048:+4G --typecode=1:ef00 --new=2:0:0 \
  --typecode=2:8300 "$work/disk.raw" >/dev/null
loop="$(losetup --find --show --partscan "$work/disk.raw")"
udevadm settle
test -b "$loop"p1
test -b "$loop"p2
mkfs.vfat -F 32 "$loop"p1 >/dev/null
printf '%s' 'harbor-ci-only-test-passphrase' > "$work/key"
chmod 600 "$work/key"
cryptsetup luksFormat --type luks2 --batch-mode \
  --pbkdf argon2id --pbkdf-memory 16384 --pbkdf-parallel 1 --iter-time 150 \
  --key-file "$work/key" "$loop"p2 >/dev/null
luks="$(cryptsetup luksUUID "$loop"p2)"
mapper="luks-$luks"
cryptsetup open "$loop"p2 "$mapper" --key-file "$work/key"
mkfs.btrfs -qf "/dev/mapper/$mapper"
mkdir -p "$work/root" "$work/top"
mount -t btrfs -o subvolid=5 "/dev/mapper/$mapper" "$work/top"
btrfs subvolume create "$work/top/@" >/dev/null
btrfs subvolume create "$work/top/@home" >/dev/null
mount -t btrfs -o subvol=/@ "/dev/mapper/$mapper" "$work/root"
echo 'Extracting genuine pinned CachyOS rootfs (no host filesystem modifications)...'
7z e -so "$iso" arch/x86_64/airootfs.sfs > "$work/rootfs.sfs"
unsquashfs -force -d "$work/root" "$work/rootfs.sfs" >/tmp/harbor-uefi-unsquash.log
version="$(find "$work/root/usr/lib/modules" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | grep -E 'cachyos$' | sort -V | tail -n 1)"
test -n "$version"
echo "REAL_CACHYOS_MODULE_ABI=$version"
mkdir -p "$work/root/boot" "$work/official-kernel"
mount -t vfat "$loop"p1 "$work/root/boot"
7z e -y -o"$work/official-kernel" "$iso" \
  arch/boot/x86_64/vmlinuz-linux-cachyos >/dev/null
cp "$work/official-kernel/vmlinuz-linux-cachyos" \
  "$work/root/boot/vmlinuz-linux-cachyos"
cat > "$work/root/etc/mkinitcpio.conf" <<'MK'
MODULES=(btrfs dm_mod dm_crypt virtio_pci virtio_blk)
BINARIES=()
FILES=()
HOOKS=(base systemd modconf keyboard sd-vconsole block sd-encrypt filesystems fsck)
COMPRESSION="zstd"
MK
btrfsid="$(blkid -s UUID -o value "/dev/mapper/$mapper")"
espid="$(blkid -s UUID -o value "$loop"p1)"
cat > "$work/root/etc/fstab" <<FSTAB
UUID=$btrfsid / btrfs defaults,subvol=/@ 0 0
UUID=$btrfsid /home btrfs defaults,subvol=/@home 0 0
UUID=$espid /boot vfat defaults 0 2
FSTAB
printf 'CachyFresh\n' > "$work/root/etc/hostname"
printf '%032x\n' 1024 > "$work/root/etc/machine-id"
mkdir -p "$work/root/etc/systemd/system"
ln -sfn /usr/lib/systemd/system/multi-user.target \
  "$work/root/etc/systemd/system/default.target"
mkdir -p "$work/root/etc/systemd/system/multi-user.target.wants"
ln -sfn /usr/lib/systemd/system/serial-getty@.service \
  "$work/root/etc/systemd/system/multi-user.target.wants/serial-getty@ttyS0.service"
for dir in dev dev/pts proc sys run; do mkdir -p "$work/root/$dir"; done
mount --rbind /dev "$work/root/dev"
mount -t proc proc "$work/root/proc"
mount --rbind /sys "$work/root/sys"
mount --bind /run "$work/root/run"
if ! chroot "$work/root" /usr/bin/mkinitcpio -k "$version" \
  -g /boot/initramfs-linux-cachyos.img > "$work/mkinitcpio.log" 2>&1; then
  tail -n 65 "$work/mkinitcpio.log"
  exit 73
fi
test -s "$work/root/boot/initramfs-linux-cachyos.img"
curl -fLsS --retry 3 --max-time 160 \
  https://archive.archlinux.org/packages/l/limine/limine-12.8.0-1-x86_64.pkg.tar.zst \
  -o "$work/limine.pkg.tar.zst"
echo "337744a1abfc827fc17c02ec3c153eacf17ecc5714643e1767ae8000286105d1  $work/limine.pkg.tar.zst" |
  sha256sum -c -
mkdir "$work/limine"
bsdtar -xf "$work/limine.pkg.tar.zst" -C "$work/limine"
efi="$(find "$work/limine" -iname 'BOOTX64.EFI' | head -n 1)"
test -f "$efi" || { echo LIMINE_EFI_NOT_FOUND; exit 74; }
mkdir -p "$work/root/boot/EFI/BOOT"
cp "$efi" "$work/root/boot/EFI/BOOT/BOOTX64.EFI"
# New inactive restored root leaves original @ intact.
btrfs subvolume snapshot "$work/top/@" "$work/top/@harbor-88888888-root" >/dev/null
printf 'CachyRestored\n' > "$work/top/@harbor-88888888-root/etc/hostname"
sed -i 's|subvol=/@ |subvol=/@harbor-88888888-root |' \
  "$work/top/@harbor-88888888-root/etc/fstab"
cat > "$work/top/@harbor-88888888-root/etc/systemd/system/harbor-boot-proof.service" <<'PROOF'
[Unit]
Description=Harbor restored system boot proof
After=local-fs.target
[Service]
Type=oneshot
ExecStart=/usr/bin/sh -c 'echo HARBOR_CACHYOS_RESTORED_UEFI_LUKS2_BOOT_OK > /dev/ttyS0'
[Install]
WantedBy=multi-user.target
PROOF
ln -sfn /etc/systemd/system/harbor-boot-proof.service \
  "$work/top/@harbor-88888888-root/etc/systemd/system/multi-user.target.wants/harbor-boot-proof.service"
cat > "$work/root/boot/limine.conf" <<LIMINE
timeout: 1
default_entry: 2
/+Harbor restore
  //CachyOS-Restored
  protocol: linux
  path: boot():/vmlinuz-linux-cachyos
  module_path: boot():/initramfs-linux-cachyos.img
  cmdline: rw console=ttyS0,115200n8 rootflags=subvol=/@harbor-88888888-root rd.luks.uuid=$luks root=/dev/mapper/luks-$luks
LIMINE
sync
for dir in run sys proc dev/pts dev; do
  mountpoint -q "$work/root/$dir" && umount -l "$work/root/$dir"
done
umount "$work/root/boot"
umount "$work/root"
umount "$work/top"
cryptsetup close "$mapper"
mapper=""
losetup -d "$loop"
loop=""
cp /usr/share/OVMF/OVMF_VARS.fd "$work/OVMF_VARS.fd"
echo HARBOR_GENUINE_CACHYOS_VM_BOOT_ATTEMPT
python3 tests/qa_cachyos_uefi_guest_expect.py "$work/disk.raw" \
  "$work/OVMF_VARS.fd" "$work/serial.log"
echo PASS_ACTUAL_CACHYOS_RESTORED_UEFI_LUKS2_LIMINE_BOOT
