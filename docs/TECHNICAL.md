# ⚙️ Technical reference

[← Home](../README.md) · [Setup and recovery](WORKSTATION_BACKUPS.md)

**How it works.** Btrfs Assistant Harbor combines the upstream GPL Btrfs/Snapper UI, a Rust content-addressed backup engine and an optional independent legacy checkpoint-v2 backend. CAS archives use one repository root \`Workstations/\`: a \`.harbor-repo-id\` marker, one \`objects/\` FastCDC/BLAKE3+zstd pool and per-machine \`machines/<name>/manifests/\`. Snapshots are identified and verified; matching chunks written by supported Linux clients are reused.

**Existing NFS directory:** select the already-mounted root; do not make a \`Workstations/Workstations/\` subrepository or independent \`Pegasus/\` and \`Galactica/\` CAS pools. If CAS metadata is missing, *initialize metadata in that existing root* once, preserving existing folders. Always positively verify the mounted NFS server/export before sending: mounting failures must not silently redirect a backup to a local placeholder. The Rust CLI \`harbor-transport init --repo /path/to/Workstations\` creates only CAS control metadata. Archive commit happens only after full stream verification.

**Safety:** network NAS writes and reads are permitted, but destructive global CAS garbage collection via NFS/SMB/SSHFS/9p is refused. Local GC requires a preview plus a matching plan SHA. Do not overwrite live root on restore: use a new, empty Btrfs staging directory.

**Limits:** Linux x86-64 with real Btrfs readonly snapshots. The current Galactica label in synthetic tests denotes a *Linux guest*, **not** a Mac backup. Native macOS/APFS capture, secure distributed GC and encrypted/multi-root ReaR bare-metal rescue require separate development; no misleading support claim.

**Verified scope:** 0.1.0 Linux stable CI includes Rust, Qt/Python, real loopback Btrfs/Snapper, two Linux QEMU guests, cancel/restart send, 1000-cycle CAS endurance and Debian 13, Fedora 44, Arch packages. See [exact scope](validation/QA_LINUX_STABLE_SCOPE_2026-10-22.md), [multi-machine CAS](CAS_MULTIMACHINE_2026-10-21.md) and [test evidence](VALIDATION.md). Source: [main repository](https://github.com/GodsQuantum/BTRFS-Assistant-Harbor).
