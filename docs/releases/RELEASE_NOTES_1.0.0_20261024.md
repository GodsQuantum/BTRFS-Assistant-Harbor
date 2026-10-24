# Btrfs Assistant Harbor 1.0.0

Linux x86-64 production release, only within the qualified scope.

## What is included

- Qt6 Btrfs Assistant 2.3.2 baseline, EN/FR/zh-CN.
- Guarded remote snapshot transfers (Btrfs/NFS/SMB/SSH), verified
  archive metadata and resume, and Rust content-addressed storage.
- Native systemd scheduling; optional shutdown only after a successful
  backup, scoped to the correct profile on shared storage.
- Contextual tray only for active background backup with GUI closed.
- Whole-machine catalogs and EFI capture, with restore preflight and
  separately staged restore tools.

## What 1.0.0 does NOT promise

No universal one-click bare-metal restoration guarantee. Secure Boot,
LUKS/LVM/RAID, multi-root, systemd-boot, and destructive network
CAS garbage collection remain unverified/unsupported. Full end-to-end
recovery is demonstrated on disposable UEFI+GRUB+single-Btrfs-root
VMs only. Always retain another independent recovery method.

## Upgrade from 0.1.x

Native Arch, Debian and Fedora packages upgrade without modifying
existing Snapper configs, mount points, snapshots or remote backups.
Shutdown remains opt-in; backup archive format remains compatible.

See docs/VALIDATION.md for the certification evidence and release gates.
