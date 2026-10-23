# Changelog

## 0.1.5-4 — 2026-10-23 (development candidate)

- Validate Btrfs v2 checkpoint frames, full SHA-256 and concatenated zstd in a single read (avoids an expensive double read of large NFS archives).
- Expose checksum failure reasons and a distinct backup-verification phase in the tray.
- Update Arch/CachyOS and Fedora candidate builds, without changing machine identity or existing backup data.

## 0.1.1 — 2026-10-22

- ⚓ Canonical Harbor anchor, ink/teal palette and brand identity in Qt, desktop menu, AppStream metadata and README.
- 🌍 New English, French and Simplified Chinese landing pages, concise features, documented support boundaries and verified release links.
- 📦 Versioned native Arch/CachyOS, Fedora 44 and Debian 13 packages. CI upgrades from the stable 0.1.0 baseline.
- 🧪 Tests ensure brand assets, desktop icons and translations stay consistent.

## 0.1.0 — 2026-10-22

- Linux x86-64 stable release: Qt/Snapper, Rust CAS full and incremental Btrfs backups, multi-machine shared repository, staged recovery.
- Verified QEMU send/receive, GUI cancellation, 1,000 CAS cycles, concurrent writers and distro package lifecycle.
- Fail-closed process execution and local-only destructive CAS GC guard.

[Releases](https://github.com/GodsQuantum/BTRFS-Assistant-Harbor/releases) · [Validation](docs/validation/QA_LINUX_STABLE_SCOPE_2026-10-22.md)
