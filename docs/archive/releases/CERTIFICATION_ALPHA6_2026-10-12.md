# Btrfs Assistant Harbor alpha6 — certification evidence

Goal: detect backup and restore failures before the first user trial.
Never mistake an isolated guest result for proof on physical Pegasus.

## New alpha6 regressions

Two tests first failed on the frozen alpha5 code:
- test_multi_hour_cas_transfers_are_not_killed_by_python_timeout:
  scheduled Btrfs sends used timeout=7200, inappropriate for >300 GiB.
- test_long_archive_verification_is_not_killed_after_180_seconds:
  integrity checks used timeout=180 and could reject valid large archives.
- harbor-release-version CTest failed: Qt reported 0.1.0-dev, not alpha5.

Alpha6 removes arbitrary subprocess deadlines for send and verification.
The systemd unit owns service cancellation; bounded network retry and
exclusive repo locks are still in place. The Qt version is now alpha6.
Two new Python regression tests and one CTest have passed post-fix.

## Existing alpha5 laboratory evidence retained

CAS: FastCDC+zstd, BLAKE3 and SHA256, full readback before manifest
publication, corrupted object rejected. QEMU real Btrfs: complete and
incremental send and receive, parent chains, byte-for-byte restore,
UID1000. Isolated NFSv3, NFSv4.1 and SMB3 real client/server mounts:
server paused after several objects, resumed, restored identical files,
no unsafe fallback to a local directory after mount disappearance.

## Hard boundaries — do not claim total certification

1. Real Pegasus GUI and the user's actual Snapper inventory were not
   tested; only Cloud9 LXC700 was authorized.
2. Complete EFI/boot/bare-metal multi-subvolume restoration is not
   equivalent to sending an individual root Snapper snapshot and has
   not been implemented as a one-click comprehensive recovery.
3. CAS has no automatic retention or garbage collector yet. Monitor
   disk capacity; do not delete backup parents or historical archives.
4. Production NFS owner/ACLs of root-run legacy scheduled checkpoint-v2
   writes are not independently certified. CAS writes with UID1000
   were verified in a guest, but export behavior can differ.
5. The removal of fixed deadlines was regression tested, not yet
   performance-benchmarked on actual multi-hundred-GiB transfers.

Status: release QA candidate for a controlled test, not a certified
replacement for the user's only production backup. Preserve prior data.
