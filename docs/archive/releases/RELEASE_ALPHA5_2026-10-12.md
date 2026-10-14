# Btrfs Assistant Harbor — alpha5 release QA (12 Oct 2026)

Frozen source tag: v0.1.0-alpha5
Code commit: 5e848a02d3a397b297a91847b1c03dc711e1837b

## Native installers, independently installed and smoke-tested

- Arch/CachyOS .pkg.tar.zst: SHA256 8bd4aee035e25f6cb73ebd94d727af018e22c047a5d501a4cf450d2c6f70a9c2
- Ubuntu 26.04 .deb: SHA256 ef00c29ba028564f2333dfcd9001d943cd6c2c7c39ce5983a5f56a446816b1e6
- Fedora 44 .rpm: SHA256 ae3ba9c62a357b8bc11ede40f28df251473e34ff0ee08180c57825135545c065
- Frozen source .tar.gz: SHA256 31c8e7e767622177e255eae7767b18a6ab1ca5d57d9b058840b463bade76e4fe

Native builds and installations passed in isolated distro containers,
including Qt GUI version, both backend CLIs, Python scheduler and dynamic
dependency checks. Rust/C++/Python tests passed.

## Actual Linux NFS and SMB guest tests

NFSv3: persistent on-disk server UNFS3 + Alpine NFS client.
NFSv4.1: distinct Alpine kernel NFSd server VM backed by ext4 disk, and
Alpine NFS client VM. SMB3: Samba container and Alpine CIFS client VM.
All tested full/incremental Btrfs send and receive and checksum, server
pause/restart after real chunk writes, byte-for-byte restored data,
and refusal to write into an unmounted network destination.
Six systemd unit timer variants: systemd-analyze verify PASS.

## First graphical launch

Existing Btrfs Assistant local panels and Snapper configuration enumeration
are preserved. There is NO import or reset of local Snapper snapshots.
The new Remote backups tab selects the existing readonly snapshot, the
desired currently mounted destination path and transfer engine.
Hourly/daily/weekly schedules for legacy and CAS are available, as well
as listing and disabling schedules. A remote restore goes only into an
empty Btrfs staging path and does not activate an automatic rollback.

Limits: no automatic EFI/bare-metal recovery for all independent
subvolumes, no CAS retention/GC or built-in NFS mounting. Production
Pegasus GUI, actual production NFS ACLs and outages are NOT tested,
per explicit Cloud9-only access. Continue using existing Harbor backup
until a full restore check on the target system is completed.
