# ALPHA9 — Machine-set / EFI / multi-volume certification plan (QA-only)

This is not a claim of machine recovery certification.

## Safety model
- The original upstream Btrfs Assistant remains installed and unchanged.
- No changes to host mounts, NFS flags, ACL, production Snapper or any real backup.
- All machine-restore actions must be previewable first. The Qt alpha9 prototype
  adds **only** legacy machine-set listing and staging restore PREVIEW.
- Legacy checkpoint-v2 and Rust CAS repositories are different formats.
- `machine_set_v2.py` already sets `bootable: false` for its catalogs; this is
  **correct** because receiving Btrfs members does not reinstall UEFI boot.
- Do not expose a GUI "restore computer" button until a proven rescue-only
  workflow produces a successful boot from a blank QEMU disk.

## The upstream components to reuse
- Snapper native D-Bus `LockConfig` while a backup reads Snapper snapshots;
  this prevents deletion, but is not sufficient alone to guarantee Btrfs RO.
- Btrfs native send/receive for each source **subvolume**; snapshots are
  non-recursive, so nested /home, /var/log, swap and other independent
  subvolumes must be inventoried, not assumed to belong to root.
- ReaR for partition-table, LUKS/LVM, EFI and bootloader recovery. Use the
  **same ReaR version** at backup and rescue to avoid layout syntax drift.
  ReaR is not a substitute for verifying backed-up members and bootfiles.
- OVMF on QEMU with an *independent copy* of UEFI VARS, rather than the
  Cloud9 host EFI configuration.

## Acceptance tests required before declaring complete
| Gate | Fixture | Pass evidence |
|---|---|---|
| A1 | Arch/CachyOS guest KDE/Wayland + native Snapper | GUI parity baseline: browse, snapshot create/compare, rollback, schedule and maintenance |
| A2 | Disposable Btrfs 3-subvolume machine | Native root, home, var/log all inventoried, backed up, restored and bytewise compared |
| A3 | Nested Btrfs subvolume inside root | Separate member captured; no false assertion that a root snapshot includes it |
| A4 | GPT+EFI FAT32+root Btrfs OVMF | Destroy guest disk, ReaR reconstructs partitions and ESP, restore, UEFI boots to login |
| A5 | systemd-boot and GRUB guest configurations | Recovered kernels, initramfs, fstab and boot entries work with new PARTUUID/UUID |
| A6 | Missing EFI / unmounted persistent volume / stale UUID | Fail closed BEFORE claiming 'complete' or deleting any existing backup |
| A7 | NFSv4 server VM + two separate Linux clients | Cross-client CAS lock prevents GC during restore; after release GC works |
| A8 | Intentionally unsafe `local_lock=flock` NFS client | Lock flaw detected, destructive CAS operations denied |
| A9 | SMB server VM + two clients | Same lease/lock and reconnect tests as NFS |
| A10 | Interrupted source send and receiver receive, VM reboots | Checkpoint resumes without silently changing source UUID or orphaning partial |
| A11 | Snapshot-number reuse Snapper >=0.13.2 | Binds to Btrfs source UUID, refuses false parent matches |
| A12 | Concurrent schedule + manual request | No duplicate writers, crash-safe state, restart and progress persistence |
| A13 | Malformed JSON, symlinks, stale plan, fabricated archive | No destructive operation; UI shows actionable error, logs remain UTF-8 |
| A14 | User graphical exploratory test on explicitly authorized workstation | Final human approval before replacing Btrfs Assistant upstream |

## Alpha9 phase 1 implementation currently staged (not yet compiled)
- Qt widget displays **historical machine sets** in a dedicated list separate
  from individual backups and CAS archives.
- `set-list` calls the installed upstream Harbor checkpoint-v2 CLI directly,
  without a new daemon, custom bridge or browser.
- `set-restore` generated ONLY as a dry-run: no `--confirm` accepted from Qt,
  canonical UUID & absolute path checks, JSON results validated, catalog never
  described as bootable.
- The user must provide an empty Btrfs staging directory; the backend verifies
  its conditions without writing in dry-run mode.
- GATE: Qt cmake build and tests on LXC700 are pending due to the Proxmox
  container-stop/attach incident of 2026-10-13. No alpha9 release yet.

## Source references checked 2026-10-13
- https://btrfs.readthedocs.io/en/latest/btrfs-subvolume.html
- https://btrfs.readthedocs.io/en/latest/btrfs-receive.html
- https://btrfs.readthedocs.io/en/latest/btrfs-send.html
- https://man7.org/linux/man-pages/man5/nfs.5.html
- https://github.com/openSUSE/snapper/blob/master/doc/dbus-protocol.txt
- https://github.com/openSUSE/snapper/blob/master/package/snapper.changes
- https://github.com/rear/rear/blob/master/doc/user-guide/06-layout-configuration.md
- https://github.com/rear/rear/releases
- https://github.com/tianocore/edk2/blob/master/OvmfPkg/QEMU_PV_VARS.md
