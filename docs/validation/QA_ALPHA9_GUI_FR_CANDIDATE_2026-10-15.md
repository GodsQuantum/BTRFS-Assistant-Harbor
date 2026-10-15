# QA alpha9 — French GUI and CAS candidate — 2026-10-15

Branch: cert/alpha9-20261015-qa-hardening; NVMe workspace LXC 700 only. No stable release authorized.

## Actual tests
- French Qt source inventory from lupdate: 400 unique active strings, 402 completed French translations, 0 missing, lrelease 0 unfinished. Six incidental English occurrences of snapshot corrected to instantané; technical .snapshots directory intentionally not translated.
- SubvolumeModel DisplayRole shows localized Oui / Non, Sort retains bool. FilterLineEdit explicitly assigned localized Filtrer…. Qt test checks translator, critical CAS confirmation, read-only status and click-selectability of distant-backups tab at 946x717. 6/6 Qt tests pass on CT700 and native Debian 13 Qt 6.8.2.
- Actual Debian13 QEMU Btrfs-root EFI guest runs Qt xcb in fr_FR.UTF-8 with Xvfb. Revision 6: 25/25 commands RC0 and five XWD screenshots; revision 7: 23/23 RC0, QEMU exit 0, QT_SCALE_FACTOR=1.25, 1600x1000 framebuffer, 1183x896 window, captured screens. Paths under notes/cert-alpha9-20261015/gui-output-native-r5/ and gui-output-hidpi-r8/.
- Debian13 native package 0.1.0~alpha9-7+deb13 built inside official Debian13 container: 6/6 CTest RC0, SHA256 bb895020aa72780867525a70e1be9f4189af98ed4e28fc247471108f0eba8da3. The Rust MUSL binary inside is current version SHA256 1309125e0e0ef276f61e289331176352e403e40323dee15611d66ed704135a9b.
- Earlier isolated Debian13 package rev4 -> rev5 -> rev4 -> rev5 -> purge: 19 guest commands RC0. Upgrade of revision 7 from rev5 remains UNTESTED.
- Python 47/47; Rust all-targets and fmt/clippy strict; Qt 6/6; CAS Alpine 3.23.3 Btrfs FULL_INCREMENTAL / FAIL_CLOSED / PRUNE_RESTORE / MULTI_VOLUME passed three independent QEMU repetitions (runs 1-3 RC0). Times 26.69s, 27.16s, 27.15s; total QEMU/Python harness peak RSS 468572/460268/462240 KiB, NOT Harbor binary RAM budget. Logs: notes/cert-alpha9-20261015/bench-cas-alpine-current-20261015.
- QEMU SMB restart fault originally showed EAGAIN disguised as JSON parse error; CAS manifest read now preserves io error cause and rejects invalid JSON; new Rust tests PASS. SMB resumed transfer still NOT CERTIFIED, later run blocked by DEV700 Docker session key quota. No host Docker configuration touched.

## Open gates (do not claim stable)
- X11 screenshots for last tab sometimes captured preceding Snapper Settings even though QTest mouse navigation of exact last tab passed; genuine full-widget interactive E2E remains PARTIAL. KDE Wayland, dialogs, full accessibility/human UX review NOT TESTED.
- Fedora44 RPM and Arch/CachyOS booted VM packaging upgrades NOT TESTED; container smoke tests of previously published rev2 do not substitute.
- NFS two-client script failed first exclusive lock because flock over NFS requires write-open fd, whereas harness opened path read-only. See https://man7.org/linux/man-pages/man2/flock.2.html. Cross-client GC still forbidden.
- SMB restart/second independent client, network GC, destructive race/TOCTOU, crash/restart during send, Snapper end-to-end retention, benchmarks over real network are NOT CERTIFIED.
- SecureBoot, LUKS/LVM/RAID, multivolume-system recovery, systemd-boot and physical machines remain UNSUPPORTED and fail-closed.
- No stable tag, no modification to old GitHub alpha9 assets, no physical workstation installation, no production data/mount/NFS/SyncBridge changes.
