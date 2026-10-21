# Harbor — Release candidate certification audit (2026-10-21)

**Decision at this checkpoint:** QA-candidate only; do **not** label or tag as universal production-ready. This file records proven *supported scopes* and residual launch gates. All current-test rows apply to the exact workflow commit cited, not automatically to subsequent edits. Official historical recovery evidence is valid only while its tested recovery hook bytes remain identical.

## Reproducible GitHub pipelines

- [Harbor certification CI](https://github.com/GodsQuantum/BTRFS-Assistant-Harbor/actions/workflows/certification.yml): Rust lint/test/static MUSL; Qt/50 Python Ubuntu 24.04+26.04; FR/ZH translation coverage; actual Weston and KWin5 Wayland Qt smoke and keyboard accessibility; Debian 13 package; real Snapper Btrfs loopback; Qt GUI cancellation during native Btrfs send + retry/receive/byte comparison; 1,000 CAS cycles and memory ceiling; two isolated QEMU Linux guests Btrfs/CAS full+incremental+GC+restore. The latest successful complete run prior to the new l10n commit is [39650599083](https://github.com/GodsQuantum/BTRFS-Assistant-Harbor/actions/runs/39650599083) on `f7d14a4` (8/8 jobs).
- [Native packages Fedora/Arch](https://github.com/GodsQuantum/BTRFS-Assistant-Harbor/actions/workflows/native-packages.yml): reproducible native RPM and Arch package build, QA tests, install/remove/reinstall, hashes. Last 2/2 green [39648698059](https://github.com/GodsQuantum/BTRFS-Assistant-Harbor/actions/runs/39648698059) on `ff27c4b`; run [39650599101](https://github.com/GodsQuantum/BTRFS-Assistant-Harbor/actions/runs/39650599101) on `f7d14a4` additionally exercised Fedora44 KWin6 (Qt GUI compiled and compositor booted), but failed because CTest logs were root-owned; CI fixture fixed in later commit. Do not claim KWin6 gate PASS until the next completed job.
- Test code is in `.github/workflows/`, `tests/qa_*.py`, `tests/qa_*.sh`, Rust test modules and `tests/test_gui_user_smoke.cpp`; no Cloud9 dependency in CI execution.

## Evidence and limits by certification gate

| Gate | Proven scope | Explicitly unproven or excluded |
| --- | --- | --- |
| G01/G02/G03 | Cargo fmt/clippy -D warnings, Rust all-targets; 50 Python unittest; Qt 6 CTest; Ubuntu24/26 CI | Physical non-Linux and unlisted distros |
| G04 | Original ReaR 2.9 Debian13 UEFI x86-64 GPT+FAT32 ESP+Btrfs single-root GRUB recovery to empty VM disk, boots without rescue ISO ([R8 proof](QA_ALPHA9_REAR_R8_2026-10-15.md)); same exact restore hooks SHA256 below | ReaR on a user computer, Secure Boot, LUKS/LVM/RAID, multi-root, systemd-boot |
| G05-G08 | Native Debian13 DEB, Fedora44 RPM and Arch pkg builds, with SHA256 and package install/remove/reinstall in disposable distro runners | Lifecycle **upgrade/downgrade across different code versions** on this exact QA candidate and a GUI on an actual installed physical workstation |
| G09 | Real Qt accessibility names/focus smoke, French & Chinese UI, Weston Wayland + KDE KWin5 virtual compositor. KWin6 job is an independent test | Complete interactive Plasma desktop, HiDPI/a11y assistive technologies on user's workstation, every GUI screen |
| G10/G21 | Actual Snapper 2 readonly snapshots: create/list/diff/delete Btrfs loopback; historical Debian13 UEFI/Btrfs Snapper pre/post/undochange and cleanup 22 guest steps | Exhaustive upstream Btrfs Assistant/Harbor GUI parity for every create/diff/rollback/schedule dialog |
| G11/G12 | 2 independent Linux QEMU guests (named Pegasus and Galactica) sharing **one** CAS object pool; same payload, zero new chunks on guest2, safe global GC and byte-equal restore | A macOS/APFS backup on the real Galactica; verified multi-client destructive GC on NFS/SMB |
| G13/G14/G15 | Historical NFS4/SMB3 multi-client and crash-cold-boot tests in isolated VMs; fail-closed destructive network GC | Remote filesystem locking suitable for destructive GC; hardware powercut of disk write caches |
| G20 | Rust pinned openat/linkat/unlinkat CAS objects, reads, locks, safe GC; concurrent symlink attacks, immutable plan digest; hostile EFI tar tests | Exhaustive kernel/filesystem fuzz and every arbitrary attacker race |
| G22 | Qt GUI button cancels a **real Btrfs send** on a disposable root-owned Btrfs volume, child processes terminate, incomplete manifest absent, retry and native receive pass with exact data comparison | UX during physical abrupt suspend/reboot on real laptop |
| G23 | 10 independent ×100 CAS cycles, 1,000 rounds in 265.85 s; 2,470 chunk reuses, max child RSS 67,228 KiB, bound 512 MiB, QEMU Btrfs send/receive | 24 h soak on real KVM/NAS hardware, power consumption, hardware throughput guarantees |
| G24 | None on physical Pegasus/Galactica | Actual physical workstation install and APFS/macOS adapter unavailable |
| G26 | GitHub CI native QA candidates (no installed user packages) | **Stable blocked** until publication checklist, sufficient G09/G10 coverage and clearly scoped platform decision |

The Linux guest test identity `Galactica` is **not macOS**, and macOS does not natively use Btrfs. Users select the one `Workstations/` root. Directory tree: marker, shared `objects/`, separate `machines/<machine>/manifests/`; old top-level `manifests/` CAS remains readable.

## ReaR provenance — immutable current script hashes

- `backend/recovery/harbor-rear-restore`: `2f2c3042914535ebab2ee4a6999aaab654180b7d6c2356478dc49965f1829da2`
- `backend/recovery/harbor-validate-esp-tar`: `9a077f9f76f5895935367df8b8cc363f2600465c06694f84397c78f91b79a055`
- Same script hashes as historical R8 guest restoration evidence; any script modification invalidates this reuse until a new blank-disk guest restore passes.

## Promotion requirements and cleanup

1. Git tree clean, signed-off change record; no production backup volumes touched.
2. Both GitHub workflow runs **success on exactly the release tag candidate SHA**, including KWin6 and all release-blocking integrations. Inspect artifacts, SHA and package installation evidence; any ignored/skipped critical test blocks release.
3. Resolve or explicitly scope unsupported G09/G10/G24 cases and mark documented topology refusals; never advertise APFS/macOS, Secure Boot, encrypted or multiple Btrfs roots as supported without proof.
4. Use a prerelease/RC tag first if incomplete; **do not reuse the historical `v0.1.0-alpha9` assets**, which correspond to different code and are incompatible with Debian13.
5. Verify the exact assets downloaded from GitHub including SHA256 and trial installations on disposable distro systems before stable. Preserve existing Git history.
6. Cloud9 LXC700 source and QA evidentiary records remain intact; earlier cleanup deleted ~1 GiB *only* recreatable Harbor build/cargo caches. No mounts, ACL, production services or other projects modified.
