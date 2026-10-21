# Btrfs Assistant Harbor

**Btrfs Assistant 2.3.2 fork with Snapper-aware remote backups, a Rust CAS engine and an opt-in ReaR recovery helper.**

[Français](README.fr.md) · [Getting started](docs/guides/GETTING_STARTED.md) · [UEFI recovery](docs/guides/RECUPERATION_REAR_FR.md) · [Test status](docs/VALIDATION.md) · [Current release gates](docs/validation/RELEASE_GATES_CURRENT_2026-10-16.md) · [Project map](docs/PROJECT_MAP.md) · [Development](docs/DEVELOPMENT.md)

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

**Package compatibility checkpoint (16 October 2026):** the GitHub alpha9 rev2 DEB is **not compatible with Debian 13 (Qt 6.8.2)** and must not be installed there. The R29 candidate packages were rebuilt against each target distribution and exercised in disposable UEFI/Btrfs VMs: Debian 13 `0.1.0~alpha9-9+deb13` (rev7→rev9→rev7→rev9→purge, French X11/125% DPI), Fedora 44 `0.1.0-0.alpha9.10.fc44` (rev9→rev10→rev9→rev10→remove), and Arch Linux `0.1.0alpha9-9` (rev8→rev9→rev8→rev9→remove). See the exact version, SHA-256 and guest logs in [R29 validation](docs/validation/QA_ALPHA9_R29_GUI_CANCEL_PACKAGING_2026-10-16.md). These are **unreleased validation candidates**, not general user stable packages. Ubuntu 26.04 and full KDE Plasma/Wayland remain unverified (a Weston headless Qt smoke test passed); test each target before real installation. Open the GUI with its desktop launcher and use `harbor-transport --help` for the CAS CLI.

## Start a backup

1. Create or select an existing **read-only** Snapper snapshot.
2. In **Remote backups**, choose the Snapper configuration and snapshot, and select either checkpoint-v2 or Harbor CAS. Use **different** repository directories.
3. Specify an existing accessible destination; for CAS use **Initialize CAS destination** in a dedicated directory.
4. Click **Send selected snapshot**, then **List remote backups** and **Verify selected archive**.
5. Preview recovery only into a **new, empty Btrfs staging directory**, never the active system.
6. CAS removal always starts with a dry-run. Review the plan before an explicit confirmation; network GC remains prohibited.

### Shared CAS across multiple workstations (alpha9 candidate; not stable)

For Pegasus and Galactica, select **one common `Workstations/` repository root**, not separate machine repositories. Harbor keeps one `.harbor-repo-id` and one FastCDC/BLAKE3 `objects/` pool, while writing per-machine manifests to `machines/<machine>/manifests/`. The hostname is detected automatically and can be edited in the GUI. The Btrfs source/receiver implementation is **Linux-specific**: macOS/APFS Galactica backup and portable restore require a separate future capture adapter, and are **not implemented**.

Pruning considers all machine and legacy manifests under a repository-wide lock, preserving chunks still referenced by other machines. Destructive GC over NFS, SMB, SSHFS and 9p remains disabled until distributed locking is certified. Existing `manifests/` CAS repositories remain readable with no destructive migration. See [multimachine CAS design, tests and restrictions](docs/CAS_MULTIMACHINE_2026-10-21.md).

The ReaR rescue integration is **opt-in** and does **not** install a live /etc/rear/local.conf. Read the [rescue guide](docs/guides/RECUPERATION_REAR_FR.md) and test your exact machine topology in a VM before relying on it.

## Verification

At commit `64cc7c2`, Rust all-targets, rustfmt and Clippy strict PASS, **47 Python tests** and **6 Qt CTests** PASS (including French translation, tab navigation and cancel-process-group smoke). Debian 13 X11/125% DPI and Weston headless Wayland Qt smoke passed, along with three repeated Alpine/Btrfs CAS full/incremental runs, an in-flight SIGKILL/recovery test, real SMB3/NFS locking QA, and candidate package lifecycle VMs for Debian/Fedora/Arch. On 14 October 2026 the product's ReaR helper passed the **real ReaR 2.9** sequence: generate rescue ISO in Debian 13, boot on a blank QEMU disk, rebuild GPT/ESP/Btrfs, invoke the Harbor restore, rebuild both EFI GRUB loaders automatically, reboot without the ISO and verify restored data with exit code 0.

**Additional real QA:** Debian 13 Snapper number retention, pre/post diff and undochange passed 22 guest commands and QEMU exit 0. Older R30/R31 receive QA runners exited RC1 due to fixture/timing faults, and those failures remain preserved. Subsequent isolated tests **R31b (send), R32 (receive) and R33 (local GC)** each killed the entire running QEMU VM process during real Btrfs work, cold-booted the same disk, rejected unsafe staging or stale GC plans and restored retained content (all Python harness /usr/bin/time exit 0). See [Snapper/receive evidence](docs/validation/QA_ALPHA9_R32_SNAPPER_RECEIVE_2026-10-16.md) and [new QEMU power-loss evidence](docs/validation/QA_ALPHA9_R33_QEMU_POWERLOSS_EVIDENCE_2026-10-16.md).

**Not certified:** complete parity of GUI workflows with upstream Btrfs Assistant and Snapper, end-to-end Qt cancellation during an active real Btrfs transfer, extended CPU/RAM/I/O soak, KDE Plasma Wayland and accessibility. Hardware power-loss caching behavior remains untested; Secure Boot, encryption/RAID/LVM, multi-root system recovery, destructive CAS NFS/SMB GC and physical machines remain unsupported without their own tests. See [validation and evidence](docs/VALIDATION.md).

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
