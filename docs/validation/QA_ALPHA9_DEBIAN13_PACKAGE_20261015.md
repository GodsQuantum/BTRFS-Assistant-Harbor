# QA Debian 13 — alpha9 native package (2026-10-15)

Scope: real Debian 13 QEMU package operations only; not a stable release certificate.

- Base public alpha9: commit 84159a0174c5785c41927d440c81f075f86d21a2; published DEB rev2 SHA256 a1d1886e4fe9f321753bfd263a8be03cbb0ecc0a34acbb08654b02b0103d31a4.
- Source: cert/alpha9-20261015-qa-hardening; earlier hardening commits bc9d23c, a3a1647.
- Native builder: official Debian 13.7 slim, Qt 6.8.2, CMake/Ninja, Debian dpkg-shlibdeps; source bind read-only.
- Qt filter API guarded: Qt 6.8 invalidateRowsFilter, Qt >=6.10 beginFilterChange/endFilterChange. Upstream: https://doc.qt.io/qt-6/qsortfilterproxymodel.html
- CTest 6/6 PASS native Qt 6.8.2; CTest 6/6 PASS DEV700 newer Qt.
- Native DEB 0.1.0~alpha9-4+deb13 SHA256 1e6395428e30a425a52bb66d4bf20422e216a00006995694e6830edd7113d581. Depends on libqt6core6t64 >=6.8.2.
- Staged Rust static R7b transport binary SHA256 843c90c166bf9237b2254ddfdf69916b27ef756d7bbd27893ce0f55a8f593915; Qt container did not recompile Rust.
- Prior QEMU R3 published rev2 install FAIL RC100 (Qt 6.10.2 dependency unavailable). Preserve this failure.
- QEMU R4: separate QCOW2 overlay on R7b reference, ISO offline read-only; Debian 13 UEFI/Btrfs/VFAT preflight RC0 and native DEB install RC0. R4 post-install check failed RC1 due to erroneous Python harness quoting, not failed APT install.
- QEMU R5: further disposable overlay; dpkg exact version RC0; Qt GUI binary version RC0; Rust CLI help RC0; EFI helper and recovery hook presence RC0; Qt dynamic library presence RC0; APT reinstall RC0; APT purge RC0; hook absent after purge RC0; guest QEMU process exit 0.
- Exact private evidence: notes/cert-alpha9-20261015/build-debian13-native-r2.log; vm-debian13-package-r3/r4/r5/{qa-results.log,serial.log,qemu-command.txt}; harbor-debian13-offline-sha256.txt; vm-deb-install-alpha9-20261015-v3/v4/v5.py.
- Does NOT validate code-distinct upgrade/downgrade, KDE Wayland/X11 GUI, full French coverage, Ubuntu 26.04 VM, Fedora44 VM, Arch VM, new ReaR recovery hook after hardening, remote destructive GC, or Secure Boot/LUKS/RAID/LVM/systemd-boot/real hardware.
- No stable release; no Pegasus or host production snapshots/mounts altered.
