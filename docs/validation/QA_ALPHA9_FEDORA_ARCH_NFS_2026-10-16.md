# Harbor alpha9 candidate — native Debian/Fedora/Arch QA, NFS and GUI FR

**Checkpoint:** 2026-10-16, CT700 DEV NVMe only. Branch `cert/alpha9-20261015-qa-hardening`. No stable release or real-machine installation.

## VM/package identity

| VM | OS / kernel | Candidate | Actual installation/upgrade/downgrade/re-upgrade/uninstall | Status |
|---|---|---|---|---|
| Debian 13 x86_64 UEFI/Btrfs | Qt 6.8.2 | `0.1.0~alpha9-7+deb13` | Candidate installed in actual X11 VM; earlier rev4→rev5→rev4→rev5→purge 19 commands RC0. **Upgrade of rev7 from old rev5 not yet reproduced.** | PARTIAL |
| Fedora Cloud 44 x86_64 UEFI/Btrfs, kernel 6.19.10 | Qt 6.11.2, Rust 1.99, Fedora 44 DNF5 | `0.1.0-0.alpha9.7.fc44` | Published rev2 actual VM DNF install/CLI RC0 → compile current candidate with CMake+ninja and Cargo RC0 → Qt CTest 6/6 and Rust all-targets PASS → native RPM rpmbuild RC0 → DNF upgrade RC0 → rollback rev2 RC0 → reupgrade rev7 RC0 → DNF remove RC0, package absent and recovery helper absent. | PASS (scoped to RPM lifecycle and tests) |
| Arch Linux 2026-10-15 cloudimg x86_64 UEFI/Btrfs, kernel 7.2.9 | Qt 6.12.0 | `0.1.0alpha9-7` | Published rev2 actual VM pacman install/CLI RC0 → actual makepkg from current source and Rust with test suite RC0 → pacman upgrade RC0 → downgrade rev2 RC0 → reupgrade rev7 RC0 → pacman -R RC0; package absent and helper removed. | PASS (scoped to Arch lifecycle and tests) |

Official VM image SHA256:
- Fedora `28680fe5b371a5a82ebf43a31926e086a168e59949d03969c5093e7071f90b7f` (Fedora CDN cloudimg 44 1.7).
- Arch `08754e28d91b1680086c6211ef4df13559e766fff7cdb4006489b14b5d281f08` (Arch official mirror, 2026-10-15 build).
- Native Debian package: `bb895020aa72780867525a70e1be9f4189af98ed4e28fc247471108f0eba8da3`.
- Native Fedora RPM: `07bcc368b397b358861c7535bbaa8ff6da3618193df7a371e3182fb896f54f07`.
- Native Arch package: `a7040bd185cd56a7e39ed46c205ca36af9a51bbd40052f20af774ffbb3c96ca4`.
- Rust statically linked current candidate `1309125e0e0ef276f61e289331176352e403e40323dee15611d66ed704135a9b`.
- Local candidate artifacts and `SHA256SUMS`: `notes/cert-alpha9-20261015/candidate-package-artifacts/` (not public stable release).

## GUI French

- Source `lupdate` 400 distinct active strings, 402 completed catalog messages, none unfinished, source missing 0. Terminology « instantané » harmonized. UI model: localized Oui/Non for read-only, Qt sorting stays boolean; filter placeholder Filtrer…
- Debian 13 real X11 + fr_FR.UTF-8 + Qt xcb GUI screenshot pass 25/25 commands; 125% scaling pass 23/23; keyboard `Ctrl+Tab`×4 in full application **did display the actual Sauvegardes distantes page**. Previous xdotool coordinate clicks hit the preceding Snapper page due to harness coordinate assumptions; the functional Qt tab mouse test also passed.
- Full application keyboard screen proof `notes/cert-alpha9-20261015/gui-output-keyboard-r9/review-remote-by-keyboard.{xwd,png}`, associated guest log `vm-debian13-gui-x11-r9-keyboard/qa-results.log`, QEMU exit 0.
- KDE/Wayland, screen-reader and physical-device compatibility not certified. Do not claim these.

## NFS actual inter-client lock

- Disposable isolated Linux kernel NFSv4 server + two Alpine QEMU clients with distinct client IDs and common NFSv4 mount. Lock file opened read-write (NFS exclusive flock requires a writable fd). `flock` exclusivity from independent client confirmed; script RC0 and explicit `PASS NFSV4 CROSS-CLIENT flock EXCLUSION (2 distinct clients)`.
- Proof `notes/cert-alpha9-20261015/nfs4-two-client-r18.log`, script `notes/qa-nfs4-two-clients-r18.py`. `local_lock=flock` bypass not demonstrated; this part inconclusive. **No destructive NFS/SMB GC certified.**

## Not yet a global stable approval

SMB3 in-flight outage, two-client SMB locking, network destructive GC, random process kills/power cuts while CAS send/receive/GC, real Snapper retention schedules, system recovery other than the ReaR single-root GRUB non-Secure-Boot, KDE Wayland and physical devices still have open coverage. Block stable release unless expressly narrowed and fail-closed by code.
