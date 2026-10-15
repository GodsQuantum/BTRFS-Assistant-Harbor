# Alpha9 certification — French UI and Debian 13 package upgrade (15 Oct 2026)

## Scope / builds

Branch `cert/alpha9-20261015-qa-hardening`, baseline `07f59396aae4bc853c183eb19b5f4ff4ae5ccb99`. The existing GitHub alpha9 tag and already released packages remain untouched.

- Original `translations/btrfsassistant_fr_FR.ts`: 49 finished Harbor widget messages; main Btrfs Assistant and Snapper UI untranslated.
- French catalog now includes **322 unique finished Qt entries** (273 newly added from the German catalog, one duplicate upstream `MainWindow/Number` excluded, plus 49 existing). Source strings, HTML wrappers and Qt `%1`, `%2`, etc. placeholders verified by generator; `lrelease` generated **322 finished, zero unfinished, zero duplicate warning**.
- French translation glossary was authored for Btrfs scrub, balance, Snapper, quotas, subvolumes, restore safety and file browsing. UI translation compiled into `btrfsassistant_fr_FR.qm`. Generator and source diff under `notes/fr_catalog_compose_20261015.py`, on canonical CT700 NVMe. This is a programmatically validated catalog, **not a formal independent French UX linguistic review**.
- Native Debian 13 package built against Qt 6.8.2: `btrfs-assistant-harbor_0.1.0~alpha9-5+deb13_amd64.deb`, SHA256 `e2ef2f5e140c37b21b2efb57a1157d2cd5ff51518128267da50a7c733141727c`, CTest **6/6 PASS**. Static Rust binary from R7b unchanged. Logs `notes/cert-alpha9-20261015/build-debian13-fr-rev5.log`.

## Actual Debian 13 X11 GUI

- VM with separate QCOW2 overlay on Debian13 UEFI Btrfs-root + VFAT ESP; installed native Harbor DEB; Xvfb 1440×900×24, Qt xcb actual graphical server, no real-machine mount.
- First GUI attempt PXE-failed due stale copied OVMF variables. Second R2 using pristine stock OVMF variables **15/15 guest commands RC0**: boot, APT local ISO, Xvfb, GUI process alive, `xdotool` finds **Btrfs Assistant Harbor** actual visible window **946×717**, xwd full-screen capture; QEMU process RC0. QA `vm-debian13-gui-x11-r2/qa-results.log`, screenshot `gui-output/debian13-harbor-gui.xwd`.
- Third R3 used actual generated `fr_FR.UTF-8` locale-archive from isolated Debian13 builder and newly compiled Qt French QM, installed in **disposable guest overlay only**. Locale UTF-8 asserted; Qt app logs no fallback warning; X11 window 946×717 visible, screenshot differs from R2; **17/17 RC0**, QEMU exit 0. Files `vm-debian13-gui-x11-r3-fr/qa-results.log`, `gui-output-fr/{app.log,windows.txt,debian13-harbor-gui.xwd}`.
- This is actual X11 GUI rendering in a QEMU guest with Btrfs, **not an interactive human assessment of all buttons, full Wayland/KDE, DPI scaling or accessibility**.

## Real package transition with reversible contents

- Starting with installed Debian package `0.1.0~alpha9-4+deb13` on isolated UEFI/Btrfs Debian13 guest, QEMU R6 boot using dedicated QCOW2 overlay and pristine OVMF VARS.
- Offline read-only ISO includes both old and new native DEBs plus APT dependencies; both versions installed via APT, not forced dpkg metadata manipulation.
- **19 guest commands RC0**, QEMU exit 0: initial version and French QM SHA saved; upgrade to `0.1.0~alpha9-5+deb13`; new QM SHA different; downgrade with `--allow-downgrades` to `0.1.0~alpha9-4+deb13` and old QM SHA restored; second upgrade to rev5; purge; package and installed recovery hook absent. Logs `notes/cert-alpha9-20261015/vm-debian13-upgrade-r6/qa-results.log`; harness `notes/vm-upgrade-debian13-r6.py`.
- **G06**: install, upgrade, downgrade, reinstall, uninstall/purge for Debian13 in QEMU **PASS(scope)**. Ubuntu26.04 is NOT tested; old published alpha9 DEB rev2 remains FAIL on Debian13 (Qt ABI >=6.10), so do not relabel the GitHub asset.

## Remaining

Fedora RPM and Arch/CachyOS **booted VM** package upgrade, GUI Wayland and complete interactive usability, two independent SMB clients and network restart, extended CAS interruption/disk-full fuzz, security TOCTOU races, performance repeatability and real-hardware exclusion all remain open. Unsupported Secure Boot, LUKS/LVM/RAID/multivolume-system-restore/systemd-boot stays explicitly disabled. NO STABLE tag/release authorized.
