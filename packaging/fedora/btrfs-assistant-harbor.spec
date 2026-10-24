# R29 staging: Native Fedora44 source RPM recipe, not a public release.
Name: btrfs-assistant-harbor
Version: 1.0.0
Release: 1%{?dist}
Summary: Btrfs Assistant fork with Snapper and guarded CAS backups
License: GPL-3.0-or-later AND MIT
URL: https://github.com/GodsQuantum/BTRFS-Assistant-Harbor
Source0: btrfs-assistant-harbor-1.0.0.tar.gz
BuildArch: x86_64
BuildRequires: cmake
BuildRequires: ninja-build
BuildRequires: gcc-c++
BuildRequires: qt6-qtbase-devel
BuildRequires: qt6-qttools-devel
BuildRequires: rust
BuildRequires: cargo
BuildRequires: pkgconf-pkg-config
BuildRequires: libzstd-devel
BuildRequires: btrfs-progs-devel
BuildRequires: python3
Requires: btrfs-progs
Requires: snapper
Requires: polkit
Requires: python3
Requires: python3-filelock
Requires: python3-rich
Requires: zstd
Requires: hicolor-icon-theme

%description
Btrfs Assistant Harbor snapshot management, guarded CAS and experimental
single-root UEFI GRUB recovery. Secure Boot, LUKS/LVM/RAID, multi-root,
systemd-boot and destructive network CAS GC are unsupported.

%prep
%setup -q -n btrfs-assistant-harbor

%build
export ZSTD_SYS_USE_PKG_CONFIG=1
export CARGO_BUILD_JOBS=3
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr
cmake --build build --parallel 3

%check
export ZSTD_SYS_USE_PKG_CONFIG=1
export CARGO_BUILD_JOBS=3
QT_QPA_PLATFORM=offscreen ctest --test-dir build --output-on-failure
cargo test --locked --all-targets --manifest-path transport/Cargo.toml

%install
DESTDIR=%{buildroot} cmake --install build
install -Dm644 LICENSE %{buildroot}/usr/share/licenses/btrfs-assistant-harbor/LICENSE-GPL3
install -Dm644 README.fr.md %{buildroot}/usr/share/doc/btrfs-assistant-harbor/README.fr.md

# Read-only progress observer: never starts a backup.
%post
if [ -d /run/systemd/system ]; then
    /usr/bin/systemctl daemon-reload >/dev/null 2>&1 || :
    /usr/bin/systemctl enable --now btrfs-assistant-harbor-progress.service >/dev/null 2>&1 || :
fi

%files
/usr/bin/*
/usr/lib/btrfs-assistant-harbor/
/usr/lib/btrfs-harbor/
%{_unitdir}/btrfs-assistant-harbor-job@.service
%{_unitdir}/btrfs-assistant-harbor-progress.service
/usr/lib/systemd/user/btrfs-assistant-harbor-tray.service
/usr/share/applications/btrfs-assistant-harbor.desktop
/usr/share/metainfo/btrfs-assistant-harbor.metainfo.xml
/usr/share/polkit-1/actions/org.btrfs-assistant-harbor.pkexec.policy
/usr/share/btrfs-assistant-harbor/
/usr/share/btrfs-harbor/
/usr/share/icons/hicolor/scalable/apps/btrfs-assistant-harbor.svg
/usr/share/icons/hicolor/*/apps/btrfs-assistant-harbor.png
%license /usr/share/licenses/btrfs-assistant-harbor/*
%doc /usr/share/doc/btrfs-assistant-harbor/README.fr.md

%changelog
* Thu Oct 22 2026 Harbor community <noreply@github.com> - 0.1.1-1
- Unified Harbor brand and verified native Qt icon with translated landing pages.

* Thu Oct 22 2026 Harbor community <noreply@github.com> - 0.1.0-1
- Linux x86-64 supported topology, native package and checked rollback.
- Unsupported APFS, network destructive GC and encrypted multi-root recovery remain blocked.

* Wed Oct 21 2026 Harbor QA <qa@example.invalid> - 0.1.0-0.alpha9.12
- Shared CAS multi-client locks, stale GUI request guards, restore and retention regression.
- QA candidate for cross-version installation and rollback tests, not a stable release.

* Fri Oct 16 2026 Harbor QA <qa@example.invalid> - 0.1.0-0.alpha9.10
- R29 native RPM source build, icon file ownership not directory.
- Cancel action and process-group cleanup need final VM certification.
