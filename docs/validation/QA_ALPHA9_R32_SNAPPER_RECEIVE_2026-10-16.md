# R32 Snapper / R30–R31 receive interruption — final QA checkpoint, 16 October 2026

**Source:** `64cc7c2bf802901e5a677937aff71b1116991f3d`, certification branch `cert/alpha9-20261015-qa-hardening`. **Not a stable release.** Lab is Cloud9 LXC700 NVMe only. Raw evidence outside Git in `notes/cert-alpha9-20261015/`.

## Snapper pre/post, difference and exact undo — PASS (VM scope)

Real Debian 13 x86_64 UEFI/Btrfs QEMU with dedicated disposable Snapper config: `vm-debian13-snapper-r32/qa-results.log`. All **22/22 guest commands RC0** and **QEMU exit 0**. Snapper number cleanup retained exactly the newer two of three RO snapshots with versioned contents. Then created `pre`, edited a marker, created linked `post`, inspected `list --columns number,type,pre-number,description`, verified `snapper status pre..post` detected the modified path, ran `snapper undochange pre..post /var/lib/harbor-qa-snapper/qa-marker` RC0 and rechecked exact restored file content (`VERSION_THREE`).

This demonstrates **Snapper CLI behavior on a disposable Btrfs filesystem**, not Harbor GUI equivalence to upstream Btrfs Assistant, nor automated timeline/system scheduling. G10 stays PARTIAL.

## Interrupted Btrfs receive / new staging recovery — targeted proof, harness RC1

R30 Alpine 3.23.3/QEMU TCG with actual Btrfs disk, static MUSL Harbor binary SHA256 `8b58055c5116693c90f4fad2255033aed1ce6cb54d34d5814afe30198259ed7d` (transport source unchanged on HEAD `64cc7c2`).

- Five prior phases passed: full+incremental send/restore, malformed stream fail-closed, local GC with parent protection, separate volume member, and SIGKILL mid-send then verified recovery of 128 MiB data. `r30-receive/result.log` and `r30-alpine-receive-soak-guest.log`.
- **Actual receive interrupted:** guest reported `ERROR: short read from stream`; a subsequent `harbor-transport receive` to the now-nonempty staging failed closed with `restore staging must be an empty absolute real directory, not system root`. Guest marker `PASS_RECEIVE_INTERRUPTION_REFUSES_NONEMPTY_STAGING`.
- **Retry into a fresh empty staging directory succeeded**; `cmp` with original 128 MiB random payload passed; guest marker `PASS_RECEIVE_RETRY_NEW_STAGING_BYTE_IDENTICAL`.
- **R30 overall exit RC1** after these assertions, because benchmark-only `apk add time` failed (Alpine image configured `main` only, package in `community`) and the Python pexpect marker subsequently timed out. Retain the failure and do not mark full runner PASS.
- R31 added Alpine community repository, but failed to catch the timing window for an in-flight receive (`QA_RECEIVE_NOT_CAUGHT_DURING_STAGING`) and timed out, **overall RC1**. This is an inconclusive timing-dependent QA harness, not a certification of physical power loss or long-load stability. Raw logs `r31-receive/`, `r31-alpine-receive-soak-guest.log`.

**Outcome:** verified interrupted receive safety in R30 guest with exact data comparison, but **G15 remains PARTIAL**: no external VM power loss/receive or GC resume and no clean overall receive+soak runner. G23 remains PARTIAL: `/usr/bin/time -v` R30 RSS includes **QEMU + Python harness**, is not Rust engine memory budget or a valid network throughput baseline.

## Official documentation cross-check

- [Btrfs receive](https://btrfs.readthedocs.io/en/latest/btrfs-receive.html): receiver marks subvolumes read-only only **after successful completion**; a receiver interrupted midstream may leave a mutable partial subvolume, so nonempty staging must be denied rather than reused.
- [Btrfs send/receive concepts](https://btrfs.readthedocs.io/en/stable/Send-receive.html): full and incremental streams, no one-to-one on-disk inode/UUID guarantees.
- [Snapper CLI](https://snapper.io/manpages/snapper.html): `pre`/`post`, status, `undochange` and three cleanup modes.
- [Snapper configurations](https://snapper.io/manpages/snapper-configs.html): retention number/timeline and age/important limits must be tested explicitly; R32 certifies only number cleanup.

## Release blockers and hygiene

Not closed: exact Harbor GUI parity with upstream and all Snapper/timer workflows (G10), whole VM power cut and receive/GC resume (G15), symlink/TOCTOU race testing (G20), graphical cancellation of a genuine active Btrfs stream (G22), long CPU/RAM/I/O soak (G23), KDE Plasma Wayland desktop and physical machine. Secure Boot, LUKS/LVM/RAID, independent multi-root ReaR, systemd-boot, and destructive CAS GC over NFS/SMB remain unsupported/denied. No stable tag or replacement of existing Btrfs Assistant.

All temporary paths are restricted to Cloud9's QA NVMe. **Do not delete ISO, restored RAW, real VM proof logs, SHA manifests, or release package candidates;** only process-specific disposable overlays/builds may be cleaned after checking that QEMU exited and parent images have no children.
## Mise à jour 16 octobre 2026, 19:15 — nouvelles preuves ultérieures
Les RC1 R30/R31 restent des faits historiques documentés. Depuis, trois bancs indépendants R31b, R32 et R33 ont prouvé des coupures brutales du **processus QEMU** au milieu de send/receive/GC, reboot du même disque virtuel, refus staging/plan périmé et contenu conservé. Les trois scripts ont /usr/bin/time Exit status 0. Rapport détaillé : [QA_ALPHA9_R33_QEMU_POWERLOSS_EVIDENCE_2026-10-16.md](QA_ALPHA9_R33_QEMU_POWERLOSS_EVIDENCE_2026-10-16.md). G15 reste strictement limité à la VM, et ne certifie pas le cache disque d’un matériel physique.
