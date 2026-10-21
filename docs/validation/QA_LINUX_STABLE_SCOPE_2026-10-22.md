# Linux 0.1.0 — scope and strict release promotion criteria (22 October 2026)

## Decision

A production designation is valid for a bounded and verified product scope. Hardware/OS combinations that the product never supports (APFS/macOS, network destructive GC, encrypted or multi-root ReaR) do not require speculative tests before a **Linux-only** stable release. They must be transparently marked unsupported and rejected by the product. Tests of real operations in reproducible CI and virtual disks are legitimate release evidence; no vendor can test every physical machine.

This file is a release gate, not retrospective proof. Do **not** tag stable until the exact candidate revision has all mandatory jobs green and all three native downloaded release package checksums verified.

## In-scope Linux x86-64 support

- OS with native Btrfs and Snapper, packaged on Debian 13, Fedora 44, Arch/CachyOS; Qt6 GUI and command line.
- CAS: one shared repository marker and BLAKE3/FastCDC object store; machine-specific manifests, incremental snapshots, global reference retention, read/verify and recovery into a new empty Btrfs staging filesystem.
- Btrfs and Snapper: readonly snapshot enumeration, creation/list/diff/delete and GUI input guards.
- Secure execution: root-owned backend constraints, no shell interpolation for snapshot paths, commands run via argv only, timeouts and failed process spawning must return errors, cancel real in-flight Btrfs send without partial commit.
- Supported ReaR subset: UEFI x86-64 GRUB + FAT32 ESP + one Btrfs root, no Secure Boot, opt-in only, VM-validated rescue ISO.
- Linux package upgrade/downgrade and independent downloaded SHA256 verifications.

## Intentionally excluded from stable

- macOS/APFS capture/restore; the mock Galactica in CI is a Linux guest, not a Mac.
- Destructive CAS GC on network filesystems without robust distributed locks; current fail-closed behavior must remain.
- Secure Boot, LUKS/LVM/RAID, multiple independent Btrfs roots, systemd-boot rescue; do not promise these topologies.
- Guarantees regarding 24-hour hardware endurance, every Linux distro, every Snapper UI interaction, screen readers on user hardware and instantaneous power-off cache durability. Report untested scope honestly.
- Automatic installation on real Pegasus, Galactica or Cloud9 production environment without an explicit deployment request.

## Promotion checks

1. Git revision clean in the **isolated certification worktree**, no stale uncommitted code used in release and separate parallel source changes left untouched.
2. Qt/Python, Cargo fmt/tests/clippy, 1,000-cycle CAS, concurrent writers, stale GC rejection, QEMU Btrfs recovery, Snapper on real loop image, KDE Wayland Qt smoke, GUI cancellation and root command timeout tests all PASS at exact SHA.
3. Debian 13, Fedora 44 and Arch native packages build, install, uninstall and complete cross-version upgrade/downgrade/re-upgrade on disposable runners with SHA-256 PASS, package metadata identifies 0.1.0 stable and executable identifies exactly the same release.
4. Publish exact stable tag 0.1.0 Linux with immutable commit mapping, full scope/exclusions, hashes, then download and verify published assets and software versions before declaring release done.
5. Historical alpha9 prerelease and existing repository/mount/backup assets remain untouched.

Earlier broad matrices requiring testing physically every user's workstation do not block this **scoped** Linux stability classification, provided these supported operations pass and unsupported features remain explicitly unavailable.
