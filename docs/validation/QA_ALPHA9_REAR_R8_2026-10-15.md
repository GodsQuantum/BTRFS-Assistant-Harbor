# Alpha9 certification branch — ReaR R8 full recovery, 2026-10-15

**Result: PASS(scope)** for an isolated Debian 13 x86_64 OVMF, GPT, VFAT ESP, single Btrfs root, GRUB2, non-Secure-Boot profile. This is NOT blanket physical-machine recovery certification.

## Provenance and immutable evidence

- Candidate Git branch `cert/alpha9-20261015-qa-hardening`, commit `ddeb18fdd2414eb46144d157647be2e1830d1e42`. Includes strict EFI tar validation security patch `bc9d23c`.
- Recovery hook file SHA256 `2f2c3042914535ebab2ee4a6999aaab654180b7d6c2356478dc49965f1829da2`.
- Strict ESP tar validator SHA256 `9a077f9f76f5895935367df8b8cc363f2600465c06694f84397c78f91b79a055`.
- Both hashes checked inside booted R8 ReaR rescue ISO **before** recovery. Same files copied from current candidate source to a disposable original-Debian overlay for `rear mkrescue`. This is not an installation of the candidate DEB in the source VM.
- Generated ISO: `notes/cert-alpha9-20261015/rear-r8-output/rear-harbor-alpha9-r8.iso`, SHA256 `71496cf8fb5ae2488fe365133655ea980e1daeaf7770d2c5ebd21cbf3aa8ecca`. `rear mkrescue`, copy and SHA check returned 0, QEMU generation guest exited 0.
- Recovery target: **new, dedicated** 7-GiB sparse raw virtual disk `notes/cert-alpha9-20261015/rear-r8-recovery-test/blank-r8-only-virtual-disk.raw`; no host block device. QEMU OVMF firmware vars separately copied. Source raw, historical R7b and physical drives remain unchanged.
- On R8 rescue boot: `lsblk` showed one empty `/dev/vda` virtual disk (7G), no `/dev/vda1`, and ISO read-only on `sr0`; in-guest precheck returned 0.
- ReaR 2.9 `recover` recreated GPT, ESP VFAT, Btrfs root and swap on this **virtual** vda, ran external Harbor restore, then reported `Finished external restore command` and `Finished 'recover'`.
- Restored disk was inspected *in rescue*: `/mnt/local` Btrfs, `/mnt/local/boot/efi` VFAT, expected marker `HARBOR_REAR_ROOT_QA_20261013`, standard and fallback EFI GRUB present, standard GRUB install log shows successful install. The two GRUB files had identical SHA256 `5263b51d325c20726ed7ecd88ba973867d302da5ce5d1487ce56f4b7efab4884`.
- Reboot test: QEMU rescue instance exited on targeted termination after systemd poweroff failed in the rescue system; **a new QEMU process was started with the restored disk only (no CD-ROM/ISO)** and its dedicated OVMF VARS. It reached Debian 13 login on serial. This is a successful disk-only boot despite the ReaR rescue shutdown warning.
- Independent R8 verifier on 2026-10-15 16:42 CEST: disposable QCOW2 backing on restored raw; no ISO attached; logged in with QA fixture credentials; **six guest assertions RC0**: EFI/Btrfs/VFAT, expected marker, kernel+initrd, dual byte-identical GRUB binaries, two GRUB-install logs. `R8_RECOVERED_SYSTEM_GUEST_LOGIN_BTRFS_UEFI_GRUB_PASS`; verifier process RC0 and QEMU gone.
- QA files: `notes/vm-rear-alpha9-r8-source-v4.py`, `notes/cert-alpha9-20261015/rear-r8-source-v4/qa-results.log`, `notes/cert-alpha9-20261015/rear-r8-recovery-test/{rear-r8-rescue.log,rear-r8-boot.log}`, `notes/vm-rear-alpha9-r8-verify.py`, `notes/cert-alpha9-20261015/rear-r8-boot-verify/{qa-results.log,serial.log}`.

## Preserve setbacks and restrictions

- R8-source first attempt: old OVMF VARS caused GRUB rescue; switched to a fresh upstream OVMF VARS file, **no production firmware settings altered**.
- R8-source second attempt: ReaR detected unusable `resolv.conf`; third attempt mistakenly wrote scalar `USE_RESOLV_CONF=no`, rejected by ReaR (expects Bash array). Fourth (v4) uses a QA-only valid array and successfully built ISO. These failed logs are retained.
- `rear recover` reported mismatch for `/etc/rear/local.conf` because QA configuration was changed for new ISO; it also reported `efibootmgr` entry creation failure, while Harbor GRUB standard/fallback files and **subsequent actual disk-only boot succeeded**. Rescue `systemctl poweroff` produced failures on some mounts; controlled termination of only that QEMU instance was used.
- ReaR recovery system wrote its own restore logs, but no direct stdout marker for tar validation appeared in the captured **serial** log; do not claim a separate live traversal attack test inside the rescue ISO on this run. Independent 8 malicious-tar tests were previously passed on the candidate.
- **Unsupported/not tested**: Secure Boot, systemd-boot, multi independent Btrfs subvolumes, LUKS, RAID, LVM, multipath, missing/corrupt CAS chunks, non-local network repositories during recovery, real laptop/NAS, other distributions, GUI post recovery. For these topologies, fail closed.
- Status of G04: **PASS(scope: Debian13 QEMU single-Btrfs-root GRUB2 UEFI non-Secure-Boot + current hook)**. General stability and other certification gates remain open. No stable tag, no installation on user workstations.

## Current candidate regression refresh (16:43 CEST)

- DEV700, branch `cert/alpha9-20261015-qa-hardening`, source commit `ddeb18f`: Rust `cargo test --locked --all-targets` RC0, `cargo fmt --check` RC0, `cargo clippy --locked --all-targets -- -D warnings` RC0.
- Python `unittest discover` first failed because bare invocation omitted the legacy vendor module from `PYTHONPATH`; no product test failed. Corrected with `PYTHONPATH=vendor/harbor-legacy:.` returned **47/47 PASS**. Retain both logs.
- Qt GUI/offscreen CTest **6/6 PASS**. This remains **not** a human desktop UX certification.
- Logs: `notes/cert-alpha9-20261015/{r8-rust-all-targets.log,r8-cargo-fmt.log,r8-cargo-clippy.log,r8-python-all.log,r8-python-all-corrected-env.log,r8-ctest-qt.log}`; QA evidence SHA manifest `notes/cert-alpha9-20261015/SHA256_CERT_R8_20261015.txt`.

## Additional Alpine Btrfs/CAS QEMU regression and cleanup (same day)

- Isolated **Alpine 3.23.3** ISO SHA256 `d91fb5c7a73528c89e0a1aa9a7d959f9deb9ca3dc5211e39bd73fd7df0d9070e`; static PIE Harbor transport binary SHA256 `843c90c166bf9237b2254ddfdf69916b27ef756d7bbd27893ce0f55a8f593915`. The Rust source has not changed since the alpha9 release tag; the binary is the same proven R7b static build.
- Reproduced `transport/tests/vm/e2e_alpine_btrfs.py` under CT700 using disposable 640MiB guest virtual Btrfs disk, `q35,accel=tcg` (CT700 has no /dev/kvm), QA ISO and explicit binary; no host mounts or NAS touched.
- All markers **PASS**: `FULL_INCREMENTAL` (with metadata comparisons), `FAIL_CLOSED` (corrupt object / missing parent), `PRUNE_RESTORE` (GC local, parent preserved, 9p GC refused), `MULTI_VOLUME` (two distinct Btrfs members). Global process **RC0**.
- QA logs `notes/cert-alpha9-20261015/r8-alpine-btrfs-cas-e2e.log` and `r8-alpine-e2e-guest.log`; QA adaptation `notes/vm-e2e-alpine-r8-tcg.py`; temporary guest workspace automatically deleted. G11/G12 advance within **this scope only**; network multi-client locking, crash/disk-full and true multi-root ReaR remain open.
- Cleanup: confirmed no R8 QEMU process, removed 5 **disposable** R8 source/verification QCOW overlays only; historical source disks, restored R8 raw virtual disk, R8 ISO, code, logs and checksum manifest are preserved. This avoids approximately 2.7GB of unnecessary QA overlay blocks on NVMe. No production storage, physical system or active service modified.
