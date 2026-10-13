#!/usr/bin/env python3
"""Disposable end-to-end UEFI+Btrfs machine backup and blank-disk recovery.

Installs Alpine on a disposable GPT+ESP+Btrfs VM disk, boots without ISO, then
backs up root Btrfs stream via Harbor and separately archives the FAT32 ESP.
Reconstructs a NEW blank VM disk and boots the restored system via fresh OVMF
variables. Disk-layout/bootloader reconstruction here is QA-scripted and DOES
NOT yet certify the production ReaR automated recovery workflow.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import pexpect

EXPECTED_ISO_SHA256 = "d91fb5c7a73528c89e0a1aa9a7d959f9deb9ca3dc5211e39bd73fd7df0d9070e"
INSTALL = r"""#!/bin/sh
set -eu
test -b /dev/vda
test ! -b /dev/vdb
test -d /sys/firmware/efi
ip link set eth0 up
udhcpc -i eth0 -q
echo https://dl-cdn.alpinelinux.org/alpine/v3.23/main > /etc/apk/repositories
apk add --no-cache btrfs-progs dosfstools grub-efi util-linux e2fsprogs >/mnt/share/apk-install.log 2>&1 || { cat /mnt/share/apk-install.log; exit 21; }
export USE_EFI=1 ROOTFS=btrfs DISKLABEL=gpt BOOTFS=vfat
export BOOTLOADER=grub KERNELOPTS="console=ttyS0,115200 rootfstype=btrfs modules=sd-mod,virtio_blk,btrfs"
export ERASE_DISKS=/dev/vda
setup-disk -m sys -k virt -s 0 /dev/vda > /mnt/share/setup-disk.log 2>&1 || { tail -70 /mnt/share/setup-disk.log; exit 22; }
blkid /dev/vda1 /dev/vda2 > /mnt/share/installed-blkid.log
test -b /dev/vda1
test -b /dev/vda2
blkid /dev/vda1 | grep -Eq '(vfat|TYPE="vfat")'
blkid /dev/vda2 | grep -Eq '(btrfs|TYPE="btrfs")'
# Alpine setup-disk has previously returned 0 on an unsupported bootloader
# name. The ESP executable, not just the installer exit status, is essential.
! grep -Eqi 'bootloader.*not supported|grub.*error' /mnt/share/setup-disk.log
mkdir -p /mnt/efi-check
mount -t vfat /dev/vda1 /mnt/efi-check
test -s /mnt/efi-check/EFI/boot/bootx64.efi || { echo EFI_FALLBACK_MISSING; exit 25; }
umount /mnt/efi-check
echo HARBOR_ALPINE_UEFI_BTRFS_DISK_INSTALLED
"""

BACKUP = r"""#!/bin/sh
set -eu
test -b /dev/vda && test ! -b /dev/vdb
ip link set eth0 up
udhcpc -i eth0 -q
echo https://dl-cdn.alpinelinux.org/alpine/v3.23/main > /etc/apk/repositories
apk add --no-cache btrfs-progs coreutils tar attr >/mnt/share/backup-apk.log 2>&1
adduser -D -u 1000 harborbackup
mkdir -p /mnt/source /mnt/esp
mount -t btrfs /dev/vda2 /mnt/source
printf 'HARBOR_ROOT_VERIFIED_20261013\n' > /mnt/source/etc/harbor-qa-marker
btrfs subvolume snapshot -r /mnt/source /mnt/source/harbor-qa-ro
btrfs property get -ts /mnt/source/harbor-qa-ro ro | grep -q 'ro=true'
mount -t vfat /dev/vda1 /mnt/esp
test -s /mnt/esp/EFI/boot/bootx64.efi
test -s /mnt/source/boot/vmlinuz-virt
test -s /mnt/source/boot/initramfs-virt
tar -czf /mnt/share/esp-root-backup.tar.gz -C /mnt/esp .
cp /mnt/share/harbor-transport /tmp/harbor-transport
chmod 700 /tmp/harbor-transport
mkdir -p /mnt/share/cas-root
export PKEXEC_UID=1000
/tmp/harbor-transport init --repo /mnt/share/cas-root --allow-local
/tmp/harbor-transport send --repo /mnt/share/cas-root --name whole-root --snapshot /mnt/source/harbor-qa-ro --experimental --allow-local --retries 0
/tmp/harbor-transport verify-stream --repo /mnt/share/cas-root --name whole-root
sha256sum /mnt/share/esp-root-backup.tar.gz > /mnt/share/esp-sha256.txt
echo HARBOR_SYSTEM_BACKUP_VERIFIED
"""
RECOVER = r"""#!/bin/sh
set -eu
test -b /dev/vda && test ! -b /dev/vdb
ip link set eth0 up
udhcpc -i eth0 -q
echo https://dl-cdn.alpinelinux.org/alpine/v3.23/main > /etc/apk/repositories
apk add --no-cache btrfs-progs dosfstools grub-efi util-linux coreutils tar attr >/mnt/share/recovery-apk.log 2>&1
printf 'label: gpt\nstart=2048,size=532480,type=C12A7328-F81F-11D2-BA4B-00A0C93EC93B\nstart=534528,type=0FC63DAF-8483-4772-8E79-3D69D8477DE4\n' | sfdisk /dev/vda > /mnt/share/recovery-partitions.log
sleep 2
test -b /dev/vda1 && test -b /dev/vda2
mkfs.vfat -F 32 /dev/vda1 >/mnt/share/recovery-efi.log
mkfs.btrfs -f /dev/vda2 > /mnt/share/recovery-root.log
mkdir -p /mnt/target
mount -t btrfs /dev/vda2 /mnt/target
cp /mnt/share/harbor-transport /tmp/harbor-transport
chmod 700 /tmp/harbor-transport
/tmp/harbor-transport verify-stream --repo /mnt/share/cas-root --name whole-root
/tmp/harbor-transport receive --repo /mnt/share/cas-root --name whole-root --staging /mnt/target --preview
test -z "$(ls -A /mnt/target)"
/tmp/harbor-transport receive --repo /mnt/share/cas-root --name whole-root --staging /mnt/target --confirm
test -s /mnt/target/harbor-qa-ro/etc/harbor-qa-marker
btrfs subvolume snapshot /mnt/target/harbor-qa-ro /mnt/target/@
default_id="$(btrfs inspect-internal rootid /mnt/target/@)"
case "$default_id" in
    ''|*[!0-9]*) echo INVALID_BTRFS_ROOT_ID; exit 33 ;;
esac
test "$default_id" -gt 5
btrfs subvolume set-default "$default_id" /mnt/target
umount /mnt/target
mount -t btrfs /dev/vda2 /mnt/target
test "$(cat /mnt/target/etc/harbor-qa-marker)" = HARBOR_ROOT_VERIFIED_20261013
# The ESP is mounted at /boot/efi, NOT /boot. Alpine's kernel and initramfs
# are inside the received Btrfs root. Mounting ESP on /boot hides them.
test -s /mnt/target/boot/vmlinuz-virt || { echo BTRFS_KERNEL_MISSING; exit 36; }
test -s /mnt/target/boot/initramfs-virt || { echo BTRFS_INITRAMFS_MISSING; exit 37; }
mkdir -p /mnt/target/boot/efi
mount -t vfat /dev/vda1 /mnt/target/boot/efi
(cd /mnt/share && sha256sum -c esp-sha256.txt) || { echo CORRUPT_ESP_ARCHIVE; exit 35; }
tar -xzf /mnt/share/esp-root-backup.tar.gz -C /mnt/target/boot/efi
test -s /mnt/target/boot/efi/EFI/boot/bootx64.efi || { echo EFI_FALLBACK_MISSING; exit 38; }
echo HARBOR_RECOVERY_ROOT_KERNEL_AND_ESP_VERIFIED
grub-install --target=x86_64-efi --efi-directory=/mnt/target/boot/efi --boot-directory=/mnt/target/boot --removable --no-nvram > /mnt/share/recovery-grub.log 2>&1 || { tail -35 /mnt/share/recovery-grub.log; exit 39; }
echo HARBOR_RECOVERY_GRUB_INSTALLED
root_uuid="$(blkid -s UUID -o value /dev/vda2)"
efi_uuid="$(blkid -s UUID -o value /dev/vda1)"
test -n "$root_uuid" && test -n "$efi_uuid"
printf 'UUID=%s / btrfs rw,relatime,subvol=@ 0 0\nUUID=%s /boot/efi vfat defaults 0 2\n' "$root_uuid" "$efi_uuid" > /mnt/target/etc/fstab
mkdir -p /mnt/target/boot/grub
cat > /mnt/target/boot/grub/grub.cfg <<EOF
set timeout=1
set default=0
menuentry 'Harbor QA recovered Btrfs root' {
    insmod btrfs
    search --no-floppy --fs-uuid --set=root $root_uuid
    linux /@/boot/vmlinuz-virt root=UUID=$root_uuid rootfstype=btrfs rootflags=subvol=@ modules=sd-mod,virtio_blk,btrfs console=ttyS0,115200
    initrd /@/boot/initramfs-virt
}
EOF
sync
umount /mnt/target/boot/efi
umount /mnt/target
echo HARBOR_UEFI_RESTORED_DISK_PREPARED
"""

def run_script_in_rescue(child: pexpect.spawn, script: str, marker: bytes,
                         timeout: int = 320) -> None:
    child.expect(b"localhost login:", timeout=230)
    child.sendline(b"root")
    child.expect(b"localhost:~#", timeout=40)
    child.sendline(b"mkdir -p /mnt/share && mount -t 9p -o trans=virtio,version=9p2000.L hostshare /mnt/share && echo SHARE_READY")
    child.expect(b"SHARE_READY",timeout=40)
    child.expect(b"localhost:~#",timeout=25)
    child.sendline(b"stty -echo")
    child.expect(b"localhost:~#",timeout=20)
    child.sendline(
        b"sh /mnt/share/" + script.encode() +
        b"; status=$?; printf '\\n__HARBOR_RESCUE_ACTION_RC:%d__\\n' \"$status\""
    )
    result = child.expect(
        [rb"\r+\n__HARBOR_RESCUE_ACTION_RC:0__\r*\n",
         rb"\r+\n__HARBOR_RESCUE_ACTION_RC:[1-9][0-9]*__\r*\n"],
        timeout=timeout,
    )
    if result != 0:
        raise RuntimeError(f"Rescue action {script} failed with nonzero exit status")
    child.expect(b"localhost:~#",timeout=35)
    print("PASS", marker.decode(), flush=True)

def run_guest(args: list[str], logfile: Path) -> pexpect.spawn:
    f=logfile.open("wb")
    child=pexpect.spawn("qemu-system-x86_64",args,encoding=None,timeout=260)
    child.logfile=f
    child._harbor_logfile=f
    return child

def terminate(child: pexpect.spawn) -> None:
    if child.isalive():
        child.terminate(force=True)
    child._harbor_logfile.close()

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--binary",type=Path,required=True)
    for key in ("iso","ovmf-code","ovmf-vars","scratch"):
        parser.add_argument("--"+key,type=Path,required=True)
    args=parser.parse_args()
    if hashlib.sha256(args.iso.read_bytes()).hexdigest()!=EXPECTED_ISO_SHA256:
        raise ValueError("ISO SHA256 mismatch")
    if not args.scratch.is_dir() or args.scratch.is_symlink() or not args.binary.is_file():
        raise ValueError("scratch and Harbor binary must exist")
    with tempfile.TemporaryDirectory(prefix=".harbor-uefi-system-disk-",dir=args.scratch) as temp:
        work=Path(temp)
        disk=work/"original-system.raw"
        subprocess.run(["truncate","-s","3072M",str(disk)],check=True)
        vars_file=work/"vars.fd"
        shutil.copyfile(args.ovmf_vars,vars_file)
        share=work/"share"
        share.mkdir()
        (share/"install.sh").write_text(INSTALL)
        (share/"backup.sh").write_text(BACKUP)
        (share/"recover.sh").write_text(RECOVER)
        shutil.copyfile(args.binary, share/"harbor-transport")
        base=[
            "-machine","q35,accel=tcg","-cpu","qemu64","-m","1024","-smp","2",
            "-drive",f"if=pflash,format=raw,unit=0,readonly=on,file={args.ovmf_code}",
            "-drive",f"if=pflash,format=raw,unit=1,file={vars_file}",
            "-drive",f"file={disk},format=raw,if=virtio",
            "-serial","stdio","-display","none","-monitor","none","-no-reboot",
        ]
        installer_args=base+["-cdrom",str(args.iso),"-boot","order=d",
            "-virtfs",f"local,path={share},security_model=none,mount_tag=hostshare,id=host0",
            "-netdev","user,id=n0","-device","virtio-net-pci,netdev=n0"]
        child=None
        try:
            child=run_guest(installer_args,work/"install-console.log")
            child.expect(b"localhost login:",timeout=230)
            child.sendline(b"root")
            child.expect(b"localhost:~#",timeout=30)
            child.sendline(b"mkdir -p /mnt/share && mount -t 9p -o trans=virtio,version=9p2000.L hostshare /mnt/share && echo SHARE_READY")
            child.expect(b"SHARE_READY",timeout=30)
            child.expect(b"localhost:~#",timeout=30)
            child.sendline(b"stty -echo")
            child.expect(b"localhost:~#",timeout=20)
            child.sendline(b"sh /mnt/share/install.sh; rc=$?; printf '\\n__HARBOR_INSTALL_RC:%d__\\n' \"$rc\"")
            # Require the standalone completion line, NOT the echoed command
            # that contains the marker before setup-disk has completed.
            outcome = child.expect(
                [rb"\r+\n__HARBOR_INSTALL_RC:0__\r*\n",
                 rb"\r+\n__HARBOR_INSTALL_RC:[1-9][0-9]*__\r*\n"],
                timeout=540,
            )
            if outcome != 0:
                raise RuntimeError("Alpine setup-disk failed in disposable guest")
            child.expect(b"localhost:~#",timeout=40)
            print("PASS GPT ESP FAT32 BTRFS ROOT INSTALLED IN VIRTUAL DISK",flush=True)
            child.sendline(b"poweroff")
            child.expect(pexpect.EOF,timeout=80)
            terminate(child)
            child=None
            boot_args=base+["-boot","order=c","-net","none"]
            child=run_guest(boot_args,work/"boot-console.log")
            child.expect(b"login:",timeout=240)
            print("PASS GPT+ESP SYSTEM DISK BOOTED VIA OVMF (ISO DETACHED)",flush=True)
            child.sendline(b"root")
            child.expect(b"#",timeout=50)
            child.sendline(b"test -d /sys/firmware/efi && findmnt -n -o FSTYPE / | grep -q btrfs && echo EFI_BTRFS_ROOT_VERIFIED")
            child.expect(b"EFI_BTRFS_ROOT_VERIFIED",timeout=30)
            print("PASS OVMF SYSTEM DISK UEFI+BTRFS ROOT VERIFIED",flush=True)
            child.sendline(b"poweroff")
            child.expect(pexpect.EOF,timeout=80)
            terminate(child)
            child=None
            child=run_guest(installer_args,work/"backup-console.log")
            run_script_in_rescue(child,"backup.sh",b"HARBOR_SYSTEM_BACKUP_VERIFIED")
            print("PASS HARBOR ROOT BTRFS CAS SEND AND ESP BOOT ARCHIVE VERIFIED",flush=True)
            child.sendline(b"poweroff")
            child.expect(pexpect.EOF,timeout=80)
            terminate(child)
            child=None
            restored_disk=work/"restored-system.raw"
            subprocess.run(["truncate","-s","3072M",str(restored_disk)],check=True)
            vars_recovery=work/"recovery-uefi-vars.fd"
            shutil.copyfile(args.ovmf_vars, vars_recovery)
            recovery_base=[
                "-machine","q35,accel=tcg","-cpu","qemu64","-m","1024","-smp","2",
                "-drive",f"if=pflash,format=raw,unit=0,readonly=on,file={args.ovmf_code}",
                "-drive",f"if=pflash,format=raw,unit=1,file={vars_recovery}",
                "-drive",f"file={restored_disk},format=raw,if=virtio",
                "-serial","stdio","-display","none","-monitor","none","-no-reboot",
            ]
            recovery_args=recovery_base+[
                "-cdrom",str(args.iso),"-boot","order=d",
                "-virtfs",f"local,path={share},security_model=none,mount_tag=hostshare,id=host0",
                "-netdev","user,id=n0","-device","virtio-net-pci,netdev=n0"]
            child=run_guest(recovery_args,work/"recovery-console.log")
            run_script_in_rescue(child,"recover.sh",b"HARBOR_UEFI_RESTORED_DISK_PREPARED",timeout=420)
            print("PASS NEW BLANK DISK PARTITIONED, ESP RESTORED, BTRFS RECEIVED",flush=True)
            child.sendline(b"poweroff")
            child.expect(pexpect.EOF,timeout=80)
            terminate(child)
            child=None
            child=run_guest(recovery_base+["-boot","order=c","-net","none"],work/"restored-boot-console.log")
            child.expect(b"login:",timeout=240)
            print("PASS RESTORED DISK BOOTED UNDER FRESH OVMF (NO ISO)",flush=True)
            child.sendline(b"root")
            child.expect(b"#",timeout=50)
            child.sendline(b"stty -echo")
            child.expect(b"#",timeout=20)
            child.sendline(
                b"test -d /sys/firmware/efi && "
                b"test \"$(findmnt -n -o FSTYPE /)\" = btrfs && "
                b"test \"$(cat /etc/harbor-qa-marker)\" = HARBOR_ROOT_VERIFIED_20261013 && "
                b"test -s /boot/vmlinuz-virt && test -s /boot/initramfs-virt && "
                b"test -s /boot/efi/EFI/boot/bootx64.efi; "
                b"status=$?; printf '\\n__HARBOR_RECOVERED_BOOT_CHECK_RC:%d__\\n' \"$status\""
            )
            verdict = child.expect(
                [rb"\r+\n__HARBOR_RECOVERED_BOOT_CHECK_RC:0__\r*\n",
                 rb"\r+\n__HARBOR_RECOVERED_BOOT_CHECK_RC:[1-9][0-9]*__\r*\n"],
                timeout=50,
            )
            if verdict != 0:
                raise RuntimeError("Restored UEFI/Btrfs root or ESP boot verification failed")
            print("PASS FULL VIRTUAL MACHINE BTRFS ROOT+ESP RESTORE AND UEFI BOOT (MANUAL DISK RECONSTRUCTION)",flush=True)
            child.sendline(b"poweroff")
            child.expect(pexpect.EOF,timeout=80)
        except BaseException:
            for filename in ("install-console.log","boot-console.log","backup-console.log","recovery-console.log","restored-boot-console.log"):
                file=work/filename
                if file.exists():
                    print(filename,file.read_bytes()[-4200:].decode("utf8","replace"),flush=True)
            for filename in ("setup-disk.log","apk-install.log","installed-blkid.log","backup-apk.log","recovery-apk.log","recovery-grub.log","recovery-partitions.log"):
                file=share/filename
                if file.exists():
                    print(filename,file.read_text(errors="replace")[-2600:],flush=True)
            raise
        finally:
            if child:
                terminate(child)

if __name__ == "__main__":
    main()
