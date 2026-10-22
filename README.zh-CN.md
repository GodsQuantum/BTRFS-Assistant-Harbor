<p align="center"><img src="branding/logo.svg" width="780" alt="Btrfs Assistant Harbor 快照锚形标志"></p>

<h1 align="center">⚓ Btrfs Assistant Harbor</h1>
<p align="center"><strong>Snapshots in. Systems back.</strong><br>
<strong>让快照拥有更安全的归宿。</strong> 在熟悉的 Btrfs Assistant 桌面界面中，将 Linux 工作站快照备份到另一块磁盘、验证数据并准备恢复。
</p>
<p align="center">
  <a href="https://github.com/GodsQuantum/BTRFS-Assistant-Harbor/releases/latest"><strong>📦 下载 Linux 版本</strong></a> ·
  <a href="docs/WORKSTATION_BACKUPS.zh-CN.md">📖 快速入门</a> ·
  <a href="docs/TECHNICAL.zh-CN.md">⚙️ 技术细节</a>
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

电脑上的 Snapper 快照可以撤销错误更新，但**只有另一块磁盘上的备份才能应对原磁盘损坏**。Harbor 将二者结合在一起。

## ✨ 为什么选择 Harbor？

- **🛟 真正保护快照。** 将 Btrfs/Snapper 快照发送到另一块磁盘或 NAS，并验证接收到的数据。
- **🧩 多台工作站，一个备份目录。** Linux 机器共享去重数据块，但每台机器的备份记录独立保存。
- **♻️ 安全地准备恢复。** 浏览和验证归档，在新的空 Btrfs 目录中演练恢复，而不是覆盖正在运行的系统。
- **🖥️ 熟悉的界面，更强的功能。** 保留 Btrfs Assistant 的快照/子卷管理，在原生 Qt 桌面中增加异机备份。

<p align="center"><img src="branding/workflow.svg" width="880" alt="从 Snapper 快照到共享验证备份和分阶段恢复"></p>

## 📸 实际桌面界面

<p align="center"><img src="docs/screenshots/remote-backups-qt6.png" width="100%" alt="真实的 Qt 6 Harbor CAS 远程备份界面"></p>
<p align="center"><em>真实 Qt 6 界面截图，来自离线测试环境，没有虚构的备份数据。</em></p>

## 🚀 三步开始

1. 从 [Releases](https://github.com/GodsQuantum/BTRFS-Assistant-Harbor/releases/latest) 下载 Arch/CachyOS、Debian 13 或 Fedora 44 的 Linux 软件包，检查 `SHA256SUMS`。
2. 打开 **Harbor → Remote backups**，选择只读 Snapper 快照和一个确实已挂载的目标目录。
3. **发送 → 验证。** 检查归档，并在单独的空 Btrfs 目录中测试恢复。

Harbor 可与原版 Btrfs Assistant **并存**；无需云账号、Docker 服务，也无需重写 Snapper 配置。

**多台 Linux 工作站共用 NAS？** 使用同一个现有 CAS 根目录，即可跨机器复用数据块并保留各自的归档。[完整配置指南 →](docs/WORKSTATION_BACKUPS.zh-CN.md)

## 🧭 明确的支持范围

支持 **Linux x86-64 / Btrfs / Snapper**。可以在 NAS 上写入和验证备份，但**禁止在 NFS/SMB 上进行破坏性的 CAS 清理**。原生 macOS/APFS 备份尚未实现，也不承诺支持加密或多根分区的整机恢复。[技术范围与验证 →](docs/TECHNICAL.zh-CN.md)

<p align="center"><strong>⚓ 保存快照，也保留恢复的选择。</strong></p>

[📖 安装与恢复](docs/WORKSTATION_BACKUPS.zh-CN.md) · [⚙️ 技术细节](docs/TECHNICAL.zh-CN.md) · [🛡️ 安全](SECURITY.md) · [🤝 贡献](CONTRIBUTING.md) · [🎨 品牌](branding/PRESSKIT.md)

<sub>本项目是 <a href="https://gitlab.com/btrfs-assistant/btrfs-assistant">Btrfs Assistant</a> 的独立 GPL-3.0-or-later 分支，不代表上游团队认可或支持。</sub>
