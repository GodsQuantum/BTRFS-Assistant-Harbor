# Btrfs Assistant Harbor: verified architecture and research (12 October 2026)

## Goal and scope

Create ONE Qt application that preserves Btrfs Assistant's upstream local
Btrfs/Snapper snapshot management. New Remote Backups tab adds manual send,
scheduled last snapshots, inventory, integrity verification and **staged**
remote restore. No duplicate local snapshot engine and no modification of
existing mount paths/configuration. Development confined to LXC 700 until
production-grade restoration, migration, NFS and SMB tests validate.

## Ownership

- **Snapper** owns snapshot numbering, creation, local pruning and local rollback.
- **Btrfs Assistant** owns local UI, comparisons and rollback dialogs.
- **Transport** owns raw immutable Btrfs send streams, storage, delivery,
  verification, remote inventory and download into separate staging.
- **Restore** must verify stream and parent chain, use native Btrfs receive
  into staging, then let Btrfs Assistant/Snapper handle activation/rollback.
  Boot, EFI and non-Btrfs files are separate features (old Harbor machine-set).
- On XFS destination (e.g. Cloud9 backup-local), no native Btrfs receive
  directly into the backup target: store sealed stream archives and restore
  back onto a Btrfs filesystem.

## Research and decisions

| Area | Upstream/technique (October 2026) | Decision / evidence |
| --- | --- | --- |
| UI and local Snapper | Btrfs Assistant 2.3.2, Qt6/C++17, GitLab tag 2026-10-09 | Fork from 069a70c; preserve GPLv3 and upstream source |
| Btrfs delta stream | btrfs-progs protocol v2 and `-p` stable parent | Retain native Btrfs metadata semantics; verify parent/source UUID before send |
| Encoded extents | `btrfs send --compressed-data` with protocol2 on supported systems | Benchmark only when both kernels/tools support it; cannot combine blindly with additional zstd |
| Compression | zstd library, fast levels and throughput/capacity modes | Per-object zstd level3 experimental default; profile selection only after measured benchmarks |
| Resume / dedup | fastcdc 5.0.0 Rust v2020 StreamCDC; BLAKE3, SHA256 | New **experimental** CAS library stores chunks immutably; abort never publishes partial manifest; rerun deduplicates common chunks even if offsets shift |
| Legacy archive format | Existing Harbor checkpoint-v2, raw .btrfs.zst and .meta | Not discarded, existing Harbor CLI remains reader; experimental CAS is a **separate format** requiring migration/compatibility adapter |
| Destination resilience | NFS/SMB mounted path; SSH dedicated receiver; systemd Persistent timers | Hardened destination identity, retry with backoff; **never write to unmounted fallback**; no mount flag modification |
| SSH security | btrbk 0.32.7 fixes CVE-2026-62943 forced-command filtering | Do not copy pre-0.32.7 SSH command filters; apply exact argv allowlists, no shell expansion |

### Important Btrfs semantics

Btrfs snapshots are not recursive. Selecting the root Snapper snapshot
does NOT send contents of nested .snapshots subvolumes, /home, /var/log,
or other independent subvolumes. Machine-level restore requires selecting
an explicit set of subvolumes and EFI/boot metadata; this is a later
migration of Harbor machine-set, not a side effect of 'send root snapshot'.

A readonly snapshot and matching UUID are necessary but **not sufficient**
to prove an identical bytewise `btrfs send` replay after interruption.
The original checkpoint-v2 requires raw-prefix SHA equality and may strand
large partials on NFS timeout. The experimental CAS design avoids this
particular constraint by using self-addressed, content-defined **finished
chunks** and publishing an ordered manifest only after a fully successful
send process. It is not a guarantee all regenerated streams share chunks:
changes in command ordering or compression may prevent deduplication. It
does not repair a corrupt or missing snapshot or disconnected source.

### Operational constraints before deployment

1. Implement remote repository identity as strongly as old Harbor's pinned
   mount fingerprint; validate **after every reconnection** without global
   remounts or NFS mount flag changes.
2. Protect Snapper source/parent from cleanup for entire transaction and
   immutable send/retry lifecycle; source must be readonly and match UUID.
3. Maintain proper UID1000 ownership/ACL semantics on NFS/SMB; do not let
   files created by root block Dolphin create/move/delete for arezki.
4. End-to-end test XFS archive -> transfer interruption -> resume -> verify
   -> Btrfs receive -> data/metadata compare, for full and incremental streams.
5. Implement chain retention (never delete an incremental parent referenced
   by a child), atomic GC, quotas, sparse files, hardlinks, Xattrs/ACL, EFI.
6. Restrict encrypted remote transport and CLI SSH command allowlists; implement
   key/auth management and optional at-rest encryption before remote release.
7. Benchmark realistic datasets, source filesystems, source CPU, NAS/NFS
   latency, SMB retry, SSH throughput, and 1TiB scale; no synthetic
   benchmark should be called real end-user throughput.
8. Qt UI must display source UUID, chain, progress (bytes and ETA), pause/
   resume/cancel, and explicit warning if experimental engine selected.

## References

- https://gitlab.com/btrfs-assistant/btrfs-assistant  (GPL v3, tag 2.3.2)
- https://btrfs.readthedocs.io/en/latest/btrfs-send.html
- https://docs.rs/fastcdc/5.0.0/fastcdc/v2020/struct.StreamCDC.html
- https://github.com/digint/btrbk/blob/master/ChangeLog
- https://security-tracker.debian.org/tracker/CVE-2026-62943
- https://github.com/berrym/btrfs-backup-ng
- https://github.com/restic/restic
- https://github.com/kopia/kopia
- https://facebook.github.io/zstd/

## Synthetic compression microbenchmark (LXC700, 2026-10-12)

32 MiB synthetic input (~50% simple repeated text, ~50% deterministic
pseudo-random data); zstd CLI 1.5.7, 2 threads, wall-clock time, no NFS
and no real Btrfs send stream. Transient test files were deleted automatically.

| Zstd level | Compressed bytes | Ratio | Throughput MiB/s |
| --- | ---: | ---: | ---: |
| 1 | 16788786 | 0.5003 | 1238.9 |
| 3 | 16790531 | 0.5004 | 922.1 |
| 7 | 16787187 | 0.5003 | 544.7 |
| 12 | 16800051 | 0.5007 | 248.9 |

On these particular bytes, zstd 1 dominated higher levels. This is
not sufficient to choose defaults for already-compressed Btrfs send,
video files, or a saturated NFS/SMB/SSH link. Never claim these numbers
represent remote link throughput or production ETA.

## Real Linux kernel Btrfs E2E: 2026-10-12 LXC700 / QEMU-TCG

A reusable rootless-on-the-host VM test was added at
`transport/tests/vm/e2e_alpine_btrfs.py` (requires QEMU, Alpine 3.23.3
virt ISO SHA-256 d91fb5c7a73528c89e0a1aa9a7d959f9deb9ca3dc5211e39bd73fd7df0d9070e,
`pexpect==4.9.0`, and an x86_64-unknown-linux-musl static Rust build).

- Alpine guest kernel **6.18.7-0-virt**, btrfs-progs 6.17.1.
- Guest-only Btrfs disk: 640MiB sparse image; 9p shared **temporary**
  directory accessible only to this QEMU test, never the production NAS.
- Created RW source subvolume with file/metadata then readonly `base`;
  edited files and created readonly `next`, both sent with
  `harbor-transport send` (full + `--parent-archive base-vm` delta).
- Both source and archived parent UUID validated by the new engine;
  stored SHA256 verified; native `btrfs receive --dump` validated both
  streams; then `harbor-transport receive --confirm` replayed them to a
  separate empty **guest Btrfs** staging directory.
- Compared actual restored files, verified received snapshot ro=true
  and nested subvolume's content **absent** (not recursive).
- Cloned archive into independent scratch, intentionally corrupted an
  object -> refused before any Btrfs receive writes; deleted parent
  manifest -> similarly refused before writes. Original repository
  re-verified intact.
- Automated PASS on exact VM full+incremental and fail-closed tests;
  35-second TCG run in this test environment (not a throughput benchmark).
- Legacy complete user data were **never mounted or written**; previously
  a separate readonly 328-byte compressed archive was also successfully
  decoded, copied into CAS, reconstructed and native-dumped.

Suggested rerun (LXC700 only, after building musl target):
```bash
python -m venv /tmp/btrfs-harbor-vm-venv
/tmp/btrfs-harbor-vm-venv/bin/pip install -r transport/tests/vm/requirements.txt
CC_x86_64_unknown_linux_musl=musl-gcc \
CARGO_TARGET_X86_64_UNKNOWN_LINUX_MUSL_LINKER=musl-gcc \
cargo build --release --target x86_64-unknown-linux-musl \
  --manifest-path transport/Cargo.toml
/tmp/btrfs-harbor-vm-venv/bin/python transport/tests/vm/e2e_alpine_btrfs.py
```

The VM script downloads a pinned Alpine ISO into a temporary working
directory only if `--iso` was not provided, validates its SHA256, and
automatically deletes the VM disk, binaries and temporary guest share
on completion or failure.

Remaining production gates: live NFS + SMB disconnect/reconnect across
a sleeping workstation, durable progress/journal UI, restore file browser,
SSH encryption and credentials, application packaging on CachyOS and
parent-chain retention/GC/space quotas. QEMU-TCG success does NOT certify
the production NFS environment or 1TB-scale behavior.

## October 12 follow-on validation and UI integration

- `RemoteBackupWidget` now supports read-only display of incomplete
  legacy `checkpoint-v2` transfers, UUID-preserving selection and manual
  resume after explicit confirmation. It uses the existing Harbor CLI,
  not the experimental CAS format. It does not force-terminate an active job.
- On the root-running Qt backend launcher, binaries located by `PATH`
  are denied unless the canonical resolved binary is regular, executable,
  owned by root, not group/world writable and under `/usr/bin` or
  `/usr/local/bin`, with safe root-owned parent directories. This
  prevents a rogue executable from a user-owned directory being launched
  with Btrfs Assistant administrator privileges. The test validates both
  a trusted system binary and unsafe paths. The trade-off is that user
  `~/.local/bin` installations of the Harbor CLI must be installed in
  a root-managed prefix before GUI activation.
- Native full + incremental restoration in QEMU now additionally compares
  sparse files byte-for-byte, verifies mode 0640, hardlink inode identity,
  symlink destination, and `user.harbor_test` extended attribute.
  Alpine guest needs `attr` tools for these assertions.
- Real VM test was repeated after enabling `verify-stream` CRC/command
  validation, and after adding metadata assertions: all succeeded with
  error injection and full guest VM teardown.
- Root/no-root snapshot source identity remains in the Rust manifest.
  Incremental restore requires a verifiable archived parent chain before
  `btrfs receive`; no automatic rollback of system root is attempted.

Production risk still open: the Qt UI presently runs the *legacy* Harbor
checkpoint backend for end-user sends/resumes; the Rust CAS is a separate
experimental command and does not transparently convert the earlier user
archive format. Live NFS/SMB reconnection/failover, source Snapper pinning
and scheduled Rust delivery must be evaluated before any engine cutover.


## Final 2026-10-12 CAS integration and ownership decisions

The GUI has a separate CAS FastCDC selector, explicit parent Snapper selection and Btrfs staging recovery. It does not silently reinterpret historic Harbor archives.

Different Zstandard encoders or levels may emit different bytes for identical raw content. A failing regression test reproduced a false checksum mismatch when reusing a valid chunk. CAS now authenticates the decoded raw block with BLAKE3 and retains the stored object's actual SHA256/size. New chunks use zstd 1.

Linux FSUID/FSGID are temporarily switched to the authenticated PKEXEC_UID only around CAS repository access. This allows the original local UID to own marker, object and manifest files without changing NFS mounts/ACL or Btrfs sender privileges. It passed isolated UID1000 root tests and Alpine QEMU send/receive tests.

The historic Python backend does not automatically inherit this CAS ownership policy, especially for systemd timers. That remains a release blocker for the strict arezki NFS permissions requirement.
