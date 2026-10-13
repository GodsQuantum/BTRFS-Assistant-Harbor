# QA alpha9 — full UEFI + Btrfs disaster recovery in isolated QEMU — 2026-10-13

## Verified
- R5 full test exited with code 0 on 2026-10-13 at 09:28 CEST.
- Original disposable VM: Alpine on GPT, ESP FAT32, Btrfs, GRUB fallback; OVMF boot succeeded with installer ISO removed.
- Harbor CAS sent and verified root Btrfs read-only snapshot stream; archived ESP FAT32 separately with SHA256.
- New blank disk and independent OVMF variables: sfdisk, mkfs.vfat, mkfs.btrfs; Harbor verified stream, previewed and received Btrfs subvolume, copied it to writable root @; restored EFI archive after checksum; reconciled fstab UUIDs; installed GRUB with Btrfs kernel path /@/boot/vmlinuz-virt.
- Installer ISO detached; fresh OVMF booted recovered disk, login reached. Final test turned off tty echo and required explicit shell exit code zero for EFI, Btrfs root, restored marker file, kernel, initramfs and EFI executable.
- Reproducible source: transport/tests/vm/e2e_uefi_btrfs_disaster_recovery.py; log logs-alpha9-20261013/qemu-uefi-full-root-esp-disaster-recovery-r5.log.

## Limits
This certifies **scripted** disk reconstruction in isolated QEMU, not ReaR automated disk/bootloader recovery or a generated ReaR ISO. No destructive network CAS GC certification, and no user hardware was touched.

## Diagnostics history
R1 missing rescue UID1000; R2 rootid parser; R3 ESP mounted on /boot masking Btrfs kernel; R4 GRUB omitted @ prefix; R5 corrected and verified. Additional source logs and findings kept in ALPHA9_JOURNAL_CONTINU.md.

## Other tests
Qt CTest 3/3, ReaR bridge pure Python 13/13, NFSv4 two distinct clients flock exclusion confirmed; local_lock variant inconclusive. Rust 50 tests, Python schedule 20 tests, Clippy, QEMU CAS full/incremental/GC had previously passed. Rerun before final release.

## Release blocker
ReaR ISO still requires trusted Harbor CLI and Python vendor dependencies plus tested EXTERNAL_RESTORE command, actual OVMF ISO boot and ReaR-driven disk re-creation. Missing ReaR install assets in alpha9. No stable release or production restore claims before this gate passes.
