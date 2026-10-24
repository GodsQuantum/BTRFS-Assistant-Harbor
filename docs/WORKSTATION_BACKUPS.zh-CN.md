# ⚓ 备份与恢复技术指南

[← 返回首页](../README.zh-CN.md) · [Technical details](TECHNICAL.zh-CN.md)

## 🛟 本地快照并不等于异机备份

Snapper 快照可以帮助回滚更改，但**同一磁盘上的快照无法抵御磁盘故障**。Harbor 基于 [Btrfs Assistant](https://gitlab.com/btrfs-assistant/btrfs-assistant) 的原生 Qt 6 界面，提供 Btrfs 只读快照传输、数据验证及独立暂存区恢复，不会自动覆盖正在运行的根文件系统。

| | 功能 |
|---|---|
| 🧭 **管理 Btrfs / Snapper** | 快照浏览、子卷管理和本地回滚。 |
| 📦 **异机备份** | 完整和增量 Btrfs 发送、校验以及专用 NFS 备份目录。 |
| 🧩 **共享 CAS 仓库** | 一个 `Workstations/` 根目录、统一数据块池、按机器隔离的清单。 |
| ♻️ **恢复传输和安全保留** | 查看中断的传输、验证归档和预览清理。**禁止在 NFS/SMB 上执行破坏性的 CAS 垃圾回收。** |
| 🔎 **分阶段恢复** | 恢复到新的空 Btrfs 暂存目录，验证通过后再决定后续步骤。 |
| 🌍 **多语言界面** | English、français、简体中文。 |

<p align="center"><img src="../branding/workflow.svg" alt="从 Snapper 快照到共享 CAS 仓库，再到分阶段恢复" width="880"></p>

## 📥 安装

从 [GitHub Releases](https://github.com/GodsQuantum/BTRFS-Assistant-Harbor/releases/latest) 下载与你的 **Linux x86-64** 发行版匹配的软件包：**Arch/CachyOS** (`.pkg.tar.zst`)、**Debian 13** (`.deb`) 或 **Fedora 44** (`.rpm`)。安装前请验证 `SHA256SUMS`。

在 Arch/CachyOS 上，进入下载文件所在目录：

```bash
sha256sum -c SHA256SUMS
sudo pacman -U ./btrfs-assistant-harbor-*-x86_64.pkg.tar.zst
```

然后从 KDE 应用菜单启动 **Btrfs Assistant Harbor**。本软件可与原版 Btrfs Assistant 并存，不会卸载原版或重写已有 Snapper 配置。

## 🚀 第一次工作站备份

1. 在 **Remote backups（远程备份）** 中选择 Snapper 配置和现有的**只读快照**。
2. 选择 **Harbor CAS** 引擎及专用的、已正确挂载的 NFS 目录。先确认挂载真实存在，以免误写入同名本地目录。
3. 对共享的 `Workstations/` 根目录执行一次 **Initialize CAS destination（初始化 CAS 目标）**。仓库包含 `.harbor-repo-id`、共享 `objects/` 和按机器独立的 `machines/<name>/manifests/`；机器名称可以修改。
4. 执行 **Send selected snapshot（发送快照）**，然后列出备份并验证归档。其他 Linux 机器可以使用同一个数据块池。
5. 在**新的空 Btrfs 暂存目录**中测试恢复；在实际机器恢复流程验证完成前，保留独立备份。

为了防止不可靠的分布式锁导致丢失数据，**NFS/SMB/SSHFS/9p 上的破坏性 CAS 清理被主动禁止**，请勿绕过。旧版 **checkpoint-v2** 与 CAS 仓库格式不能混用。

## ✅ 已验证的 Linux 范围

[Linux 0.1.0 认证范围](validation/QA_LINUX_STABLE_SCOPE_2026-10-22.md) 包括 Rust/Clippy、Qt/Python、真实 Btrfs 上的 Snapper、两个 Linux QEMU 客户端备份/恢复、取消实际 `btrfs send`、CAS 并发、1000 次循环及原生软件包生命周期。新版本须重新运行 CI。

**不支持：**原生 macOS/APFS 备份、网络文件系统上的破坏性 CAS 清理，以及包含 Secure Boot、LUKS/LVM/RAID 或多个根子卷的 ReaR 裸机恢复。可选 ReaR 仅在 UEFI/GRUB、FAT32 ESP、单一 Btrfs 根、关闭 Secure Boot 的环境中验证。未证明所有硬件、真实断电和每一种桌面配置。

## 🧰 构建与贡献

依赖：C++17、CMake、Ninja、Qt 6 Widgets/Test/LinguistTools、libbtrfsutil、btrfs-progs、Rust/Cargo、Python 3。

```bash
git clone https://github.com/GodsQuantum/BTRFS-Assistant-Harbor.git
cd BTRFS-Assistant-Harbor
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr
cmake --build build --parallel 4
QT_QPA_PLATFORM=offscreen ctest --test-dir build --output-on-failure
cargo test --locked --manifest-path transport/Cargo.toml --all-targets
```

请参阅 [贡献说明](../CONTRIBUTING.md)、[安全策略](../SECURITY.md)、[品牌规范](../branding/BRAND.md) 和 [Issues](https://github.com/GodsQuantum/BTRFS-Assistant-Harbor/issues)。

**版权与致谢：** 本项目是 **Btrfs Assistant** 的独立分支，采用 **GPL-3.0-or-later** 许可证，并不代表原项目团队支持或认可。附带的旧版 Harbor Python 组件保留各自的 MIT 许可证说明。详见 [LICENSE](../LICENSE)。


## 成功备份后自动关机

在「远程备份 → 计算机保护」中，启动手动备份前选中「备份成功完成后关闭此计算机」。定时备份可在高级选项中勾选「每次定时备份成功后关机」，然后保存定时任务。

此选项默认关闭。失败、取消或未完成的备份不得触发关机。系统使用原生 systemd 成功后操作，不以预计进度达到 100% 作为关机依据。
