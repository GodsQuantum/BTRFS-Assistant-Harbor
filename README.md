# Btrfs Assistant Harbor

**Btrfs Assistant 2.3.2 fork with Snapper-aware remote backups, a Rust CAS engine and an opt-in ReaR recovery helper.**

[Français](README.fr.md) · [Getting started](docs/guides/GETTING_STARTED.md) · [UEFI recovery](docs/guides/RECUPERATION_REAR_FR.md) · [Test status](docs/VALIDATION.md) · [Development](docs/DEVELOPMENT.md)

> **0.1.0-alpha9 — prerelease, not universal stable.** Recovery has been tested on disposable QEMU virtual disks, not arbitrary physical user hardware. Preserve a separate, verified backup. This fork installs alongside the original Btrfs Assistant.

## Features

| Area | What works | Boundary |
| --- | --- | --- |
| Btrfs and Snapper | Existing upstream snapshot browsing, local rollback, subvolume management and maintenance | Snapper owns local snapshots |
| Checkpoint v2 | Legacy Harbor remote backups, interrupted-transfer inventory and systemd schedules | This format is NOT interchangeable with CAS |
| Harbor CAS | Rust FastCDC/BLAKE3 chunk deduplication, zstd, Btrfs full/incremental send, chain validation and staged recovery | Source must be read-only Btrfs; destination a dedicated initialized repository |
| Retention | Read-only preview, explicit matching confirmation token, protection of parent archives and shared chunks | Destructive pruning on NFS/SMB is refused until verified distributed locking |
| Machine rescue | Real ReaR 2.9 ISO recovery and automatic GRUB standard/fallback repair | Only x86-64 UEFI, one Btrfs root, FAT32 ESP, GRUB, Secure Boot OFF |

The **Remote backups** tab exposes both engines, verification, recovery preview, schedules, CAS retention and historical machine-set inventory. It does not replace the original Btrfs Assistant nor reconfigure user mounts.

## Build and inspect safely

Prerequisites: Linux x86-64, C++17, CMake, Ninja, Qt6 Widgets and LinguistTools, libbtrfsutil, btrfs-progs, Rust/Cargo and Python 3. Snapper and polkit are needed for supported user workflows.

    git clone https://github.com/GodsQuantum/BTRFS-Assistant-Harbor.git
    cd BTRFS-Assistant-Harbor
    cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr
    cmake --build build --parallel 4
    QT_QPA_PLATFORM=offscreen ctest --test-dir build --output-on-failure
    DESTDIR="$PWD/staging" cmake --install build

Review the staged files, then install a distribution-compatible package only after testing it in a disposable environment. Never overwrite your existing Btrfs Assistant package.

**Package compatibility warning (15 October 2026):** the published alpha9 revision-2 DEB requires `libqt6core6t64 >= 6.10.2` but Debian 13 (Trixie) officially ships Qt 6.8.2. Installation in a disposable Debian 13 VM **failed** (`apt` exit 100). Do not force packages or falsify dependency versions: a Debian-13-native build and a real install/upgrade/purge test are required. The successful Debian 13 ReaR ISO rescue test is a separate operation and does not certify this GUI DEB. Ubuntu 26.04, Fedora and Arch package lifecycle tests remain open. Open **Btrfs Assistant Harbor** from the desktop launcher; the launcher handles privilege elevation. The separate CAS CLI documents itself via **harbor-transport --help**.

## Start a backup

1. Create or select an existing **read-only** Snapper snapshot.
2. In **Remote backups**, choose the Snapper configuration and snapshot, and select either checkpoint-v2 or Harbor CAS. Use **different** repository directories.
3. Specify an existing accessible destination; for CAS use **Initialize CAS destination** in a dedicated directory.
4. Click **Send selected snapshot**, then **List remote backups** and **Verify selected archive**.
5. Preview recovery only into a **new, empty Btrfs staging directory**, never the active system.
6. CAS removal always starts with a dry-run. Review the plan before an explicit confirmation; network GC remains prohibited.

The ReaR rescue integration is **opt-in** and does **not** install a live /etc/rear/local.conf. Read the [rescue guide](docs/guides/RECUPERATION_REAR_FR.md) and test your exact machine topology in a VM before relying on it.

## Verification

The project has passed **50 Rust tests, 39 Python tests, 5 Qt CTests including actual backup-widget interaction**, and native QEMU Btrfs transport tests. On 14 October 2026 the product's ReaR helper passed the **real ReaR 2.9** sequence: generate rescue ISO in Debian 13, boot on a blank QEMU disk, rebuild GPT/ESP/Btrfs, invoke the Harbor restore, rebuild both EFI GRUB loaders automatically, reboot without the ISO and verify restored data with exit code 0.

**Not certified:** Secure Boot, encrypted or RAID/LVM layouts, independently mounted multi-volume systems, destructive CAS pruning on NFS/SMB, all firmware/hardware, all distribution packages or large-scale production retention. See [validation and evidence](docs/VALIDATION.md).

## Project structure

- **src/** – native C++/Qt GUI, Btrfs and Snapper compatibility
- **transport/** – Rust CAS engine, integration tests
- **backend/** – checkpoint-v2 compatibility, schedules and ReaR recovery script
- **vendor/harbor-legacy/** – separately licensed legacy Python engine
- **tests/** – negative and positive checks, including end-user GUI smoke tests
- **packaging/** – distribution sources
- **docs/guides/** – use and recovery instructions
- **docs/validation/** – detailed test evidence
- **docs/archive/** – historical development notes

## Credits and license

Independent fork of [Btrfs Assistant](https://gitlab.com/btrfs-assistant/btrfs-assistant), GPL-3.0-or-later. The legacy Harbor-compatible Python component includes its own MIT license. See [LICENSE](LICENSE) and the respective vendor license. This repository does not claim upstream endorsement.
