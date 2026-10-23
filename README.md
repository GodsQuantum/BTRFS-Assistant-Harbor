<p align="center"><img src="branding/harbor-banner.png" width="100%" alt="Btrfs Assistant Harbor — snapshots and anchor"></p>

<h1 align="center">⚓ Btrfs Assistant Harbor</h1>
<p align="center"><strong>Snapshots in. Systems back.</strong><br>
<strong>Your snapshots deserve a safer place.</strong> Back up your Linux workstation, verify every transfer, and keep recovery within reach — in the Btrfs Assistant desktop you already know.
</p>
<p align="center">
  <a href="https://github.com/GodsQuantum/BTRFS-Assistant-Harbor/releases/latest"><strong>📦 Download for Linux</strong></a> ·
  <a href="docs/WORKSTATION_BACKUPS.md">📖 Get started</a> ·
  <a href="docs/TECHNICAL.md">⚙️ How it works</a>
</p>
<p align="center">
  <a href="README.md">English</a> · <a href="README.fr.md">Français</a> · <a href="README.zh-CN.md">简体中文</a>
</p>
<p align="center">
  <a href="https://github.com/GodsQuantum/BTRFS-Assistant-Harbor/actions/workflows/certification.yml"><img alt="CI" src="https://github.com/GodsQuantum/BTRFS-Assistant-Harbor/actions/workflows/certification.yml/badge.svg"></a>
  <img alt="Linux x86-64" src="https://img.shields.io/badge/platform-Linux%20x86--64-14283A">
  <img alt="Qt 6" src="https://img.shields.io/badge/desktop-Qt%206-58D6C5">
  <a href="LICENSE"><img alt="GPL 3" src="https://img.shields.io/badge/license-GPL--3.0--or--later-0B1622"></a>
</p>

---

A snapshot on your laptop protects you from a bad update. **A backup on another disk protects you from losing the laptop's disk.** Harbor brings both together.

## ✨ Why you'll want it

- **🛟 Your snapshots, actually protected.** Send Btrfs/Snapper snapshots to another disk or your NAS and verify what arrived.
- **🧩 One backup home for your workstations.** Shared storage deduplicates matching data across Linux machines without mixing up their archives.
- **♻️ No blind restore.** Review backups, verify them, and rehearse recovery in a separate empty Btrfs location.
- **🖥️ Familiar desktop, more power.** Keep Btrfs Assistant's snapshot and subvolume tools. Harbor adds a native Qt backup tab — not another server dashboard.

<p align="center"><img src="branding/workflow.svg" width="880" alt="From Snapper snapshots to shared verified backup storage and staged recovery"></p>

## 📸 The real desktop

<p align="center"><img src="docs/screenshots/remote-backups-qt6.png" width="100%" alt="Actual native Qt 6 Remote backups interface showing Harbor CAS options"></p>
<p align="center"><em>Real Qt 6 backup tab — captured in an offline test environment, with no invented backups.</em></p>

**🌍 Interface language:** choose **English**, **Français** or **简体中文** in the top toolbar. Reopen Harbor to apply your choice to every screen. The choice is saved even when Harbor runs as administrator.

## 🚀 Get started in 3 steps

1. **Download** the Linux package for Arch/CachyOS, Debian 13 or Fedora 44 from [Releases](https://github.com/GodsQuantum/BTRFS-Assistant-Harbor/releases/latest) and check its `SHA256SUMS`.
2. **Open Harbor → Remote backups.** Choose a read-only Snapper snapshot and an existing, correctly mounted destination.
3. **Send → Verify.** Confirm the archive is present and test a staged restore when convenient.

You can install Harbor **alongside** the original Btrfs Assistant. There is no mandatory cloud account, Docker runtime or replacement of your Snapper setup.

**Using one shared NAS folder?** Point every supported **Linux** workstation at the same existing CAS root. Harbor uses a single shared chunk pool with per-machine archives. [Detailed workstation guide →](docs/WORKSTATION_BACKUPS.md)

## 🧭 Know what is protected

Harbor targets **Linux x86-64 / Btrfs / Snapper**. Network-storage backup **writing and verification** are different from deletion: destructive CAS cleanup on NFS/SMB is deliberately disabled. macOS/APFS capture is not available yet, and full encrypted/multi-root system rescue is not promised. [Supported configurations & tests →](docs/TECHNICAL.md)

<p align="center"><strong>⚓ Back up the snapshot. Keep the choice to recover.</strong></p>

[📖 Setup & recovery](docs/WORKSTATION_BACKUPS.md) · [⚙️ Technical details](docs/TECHNICAL.md) · [🛡️ Security](SECURITY.md) · [🤝 Contributing](CONTRIBUTING.md) · [🎨 Brand kit](branding/PRESSKIT.md)

<sub>Independent GPL-3.0-or-later fork of <a href="https://gitlab.com/btrfs-assistant/btrfs-assistant">Btrfs Assistant</a>; no upstream endorsement. See third-party licenses.</sub>
