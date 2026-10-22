# ⚙️ 技术参考

[← Home](../README.zh-CN.md) · [Setup and recovery](WORKSTATION_BACKUPS.zh-CN.md)

**工作原理。** Harbor 保留 GPL 许可的 Qt Btrfs/Snapper 桌面功能，并增加 Rust 内容寻址备份（CAS）；旧版 checkpoint-v2 格式独立。唯一的 \`Workstations/\` 根目录保存 \`.harbor-repo-id\`、共享的 FastCDC/BLAKE3+zstd \`objects/\` 数据块池，以及 \`machines/<name>/manifests/\` 中的机器专属清单。兼容的 Linux 客户端复用相同数据块。

**现有 NFS 目录。** 直接选择已经挂载的根目录；不要创建 \`Workstations/Workstations/\`，也不要在 \`Pegasus/\` 和 \`Galactica/\` 中分别建立 CAS 对象池。如果 CAS 元数据尚未初始化，可在**现有根目录**运行一次初始化，保留已经存在的目录。写入前必须确认真实的 NFS 服务器和共享路径，避免挂载中断后误写本地占位目录。\`harbor-transport init --repo /path/to/Workstations\` 只初始化该目录的 CAS 控制数据。

**安全。** 允许在 NAS 上写入/读取备份，但拒绝在 NFS/SMB/SSHFS/9p 上执行破坏性的全局 CAS 清理。仅本地存储的清理需要预览及匹配的计划哈希。恢复时应使用新的空 Btrfs 暂存目录，禁止自动覆盖系统根分区。

**支持限制。** 目前仅支持 Linux x86-64 和真实 Btrfs 只读快照。测试中的「Galactica」是 Linux 虚拟机，**不是 Mac/APFS 备份**。原生 macOS/APFS、分布式 NAS 垃圾回收和加密/多根系统恢复尚未实现。

**验证证据。** Linux 0.1.0 的 Rust、Qt/Python、真实 Btrfs/Snapper、两台 Linux QEMU 来宾、发送取消与恢复、1000 次 CAS 循环和 Debian 13/Fedora 44/Arch 软件包均有 CI 测试。参阅[认证范围](validation/QA_LINUX_STABLE_SCOPE_2026-10-22.md)、[多机 CAS](CAS_MULTIMACHINE_2026-10-21.md) 和[测试证据](VALIDATION.md)。
