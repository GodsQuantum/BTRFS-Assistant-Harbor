# Harbor: durable jobs and calendar scheduling (2026-10-22)

## Scope

A manual CAS backup can now be launched as a persistent systemd service instance.
Only a deliberate click enables the btrfs-assistant-harbor-job@UUID.service.
Installing the package installs an INACTIVE template, no timer or backup.
Each job stores immutable source snapshot UUID, command, target, machine and
status in a root-owned directory. Journald stores progress and error messages.
Closing the Qt window hides Harbor in the tray where supported and **does not**
stop the systemd job. Explicit tray Quit requests cancellation. GUI crash leaves
the independent job running.

## Crash recovery and its limitation

On interruption, systemd retries the same command with the same source UUID,
parent UUID and repository root, including after reboot. An already committed
manifest is reverified rather than overwritten. Existing CAS objects survive
and matching chunks are reused. **The source Btrfs stream must be reread from
the beginning**: there is no guaranteed byte-offset continuation of source
reads. NFS mount presence is checked before each attempt; a local directory
with the same name is forbidden as backup target.
Missing/changed readonly snapshots cause fail-closed errors.

## Calendar / no involuntary backup

Hourly, daily and weekly schedules support precise HH:MM and, for weekly,
selected Mon..Sun. Persistent=true catches up a missed time at the next boot;
it does not operate while powered off. WakeSystem=false. Harbor timers only
transfer existing Snapper snapshots; they do not create fresh snapshots.
Nothing is automatically enabled by package installation.

## Shared CAS repository

The root is the existing Workstations/ CAS repository, with shared objects/
and machine-specific manifests. Legacy folders are preserved, and destructive
network CAS GC remains refused. FULL means a selected snapshot subvolume, not
all partitions/ESP/other subvolumes or a bootable LUKS machine image. Incrementals
use verified archived parent identities; neither an unavailable parent nor a
changed snapshot is silently accepted.

## Gates before production claim

- [ ] Actual GUI-close while REAL Btrfs send is active, service completes.
- [ ] Real systemd retry after abrupt process/power interruption.
- [ ] Lost NFS mount and recovery; no local fallback.
- [ ] UI tray cancellation kills the job cgroup; journals/state persisted.
- [ ] Complete FR/EN/ZH UI plus native packages and lifecycle tests.
- [ ] Exact SHA GitHub Actions green and package hashes.
- [ ] Pegasus package upgrade after verifying no active user transfer.
- [ ] No real Pegasus transfer/timer before user consent.
