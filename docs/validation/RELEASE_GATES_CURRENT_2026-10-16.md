# Alpha9 — release decision and next proofs (16 October 2026)

**Decision: candidate tested; stable NOT published.** New proof commit e93a370a14afbe2242d2e52fdc56fbf8afee7b76 documents G15 QEMU closure; tested transport/GUI code remains the R29 code commit 64cc7c2bf802901e5a677937aff71b1116991f3d. Git branch `cert/alpha9-20261015-qa-hardening`, HEAD `64cc7c2bf802901e5a677937aff71b1116991f3d`. Existing public tag `v0.1.0-alpha9` remains `84159a0174c5785c41927d440c81f075f86d21a2` and contains different old packages. Never reuse its assets for this commit.

## Latest exact candidate audit

- Rust all-targets, rustfmt, Clippy with `-D warnings` all RC0, 47 Python tests PASS, Qt build and CTest 6/6 RC0 (fresh 16 Oct rerun). Traces: `notes/cert-alpha9-20261015/final-20261016-late/RC` and associated logs.
- Debian 13 `0.1.0~alpha9-9+deb13` DEB SHA `3a191c555e209c881f510aec29846e6c7f480834f2ac1087c7bf82ea3c2323ca`, Fedora 44 `0.1.0-0.alpha9.10.fc44` RPM SHA `68de6e98eda15807d5496876b16f370c5d95a0aa88a237915297fab775552c05`, Arch `0.1.0alpha9-9` package SHA `2d241727bf5c3d7ac49009e07a069842579d81c4724b7a7ae1df14b0fe06a553` — rechecked 3/3 against actual files (manifest `SHA256_R29_RELEASE_CANDIDATES.txt`). Real VM package lifecycle results in [R29](QA_ALPHA9_R29_GUI_CANCEL_PACKAGING_2026-10-16.md).
- Prior R8 ReaR: real Debian13 ISO → empty GPT/Btrfs/VFAT virtual disk → external recovery → GRUB standard/fallback → OS reboot without ISO RC0. No need to rerun until recovery/boot code changes.
- Native X11 Debian13 French GUI/HiDPI, Qt process-group cancel smoke and Weston headless Wayland Qt test PASS in defined scope. Weston headless is **not** a Plasma desktop certification.
- New R32 real Debian13 Btrfs/Snapper: number cleanup 3→2, pre/post diff and `undochange`, exact marker content restored, 22 guest commands/QEMU exit RC0. New R30 guest actually interrupted Btrfs receive: partial staging refused and fresh staging data restored byte-identically, but **entire R30 harness RC1** due to absent Alpine benchmark dependency; R31 RC1 after race in receive-timing QA. See [full R32 / R30 / R31 evidence and limits](QA_ALPHA9_R32_SNAPPER_RECEIVE_2026-10-16.md). Subsequent [R31b/R32/R33 whole-QEMU power-loss tests](QA_ALPHA9_R33_QEMU_POWERLOSS_EVIDENCE_2026-10-16.md) PASS, and supersede the earlier timing-dependent G15 limitation within their defined VM scope.

## Remaining gates and scope limitations: do not call them PASSED without executing

| Gate | Needed demonstration or disposition |
| --- | --- |
| G09/G10 | Snapper real CLI pre/post/diff/undo, number cleanup PASS R32. Remaining: full GUI Btrfs Assistant parity list/create/diff/rollback/timers/dialogs/UX, accessibility and KDE Plasma Wayland separate from Weston headless smoke |
| G13 | NFS `local_lock` unsafe behavior must be explicitly denied for dangerous operations; 2 independent clients' standard NFSv4 lock already PASS |
| G15 | **PASS within isolated QEMU scope**, no longer open for virtual send/receive/GC: R31b, R32, R33 whole-QEMU SIGKILL, cold boot, fail-closed and content restoration all exit0. Real physical power loss/caches remain untested; no hardware certification |
| G20 | Path traversal/symlink/race/TOCTOU across dangerous operations, non-root and stale deletion plans; preserve fail-closed defaults |
| G22 | Click the GUI cancel button during an actual Btrfs transfer and confirm process group tree shutdown/consistent repository, plus restart/retry; current Qt QTest uses a shell child fixture |
| G23 | Isolated CPU/RAM/I/O/performance and soak benchmarks (including long-run stability and regression vs original) with versioned baseline; current 3× QEMU CAS measurements are harness overhead, not standalone engine benchmark |
| Physical / Ubuntu | Ubuntu 26.04, Plasma/KDE and actual hardware may be left NOT_TESTED/UNSUPPORTED for the initial stable only if the user-facing package/documentation excludes claims of coverage. Do not modify a real machine without authorization |

## Acceptance procedure

Report gate-specific VM logs with machine OS/kernel/Btrfs/Snapper/Qt/ReaR versions; commit; SHA of inputs/outputs; command, exit status, reproduced failure then passing retest. Never disable safety protections to obtain a PASS. Once supported gates close, regenerate distribution-native packages from the final code, rerun install/rollback/removal and security checks, sign/attest SHA, and only then consider a stable tag. If blocked, update handoff with the exact command/result and leave candidate on the QA branch.

**Use the root `MATRICE_CERTIFICATION_FINALE_2026-10-15.md` as the authoritative per-gate status.** This document is a navigational snapshot, not a substitute for current checks.