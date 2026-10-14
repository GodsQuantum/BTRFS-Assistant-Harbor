# Getting started

1. Create a read-only Snapper snapshot.
2. Open **Btrfs Assistant Harbor** and choose **Remote backups**.
3. Select checkpoint-v2 or Harbor CAS (different, incompatible repository formats).
4. Choose your Snapper configuration, snapshot and an existing destination directory; initialize a dedicated CAS repository when applicable.
5. Send, list and verify the new archive; read the progress log.
6. Preview recovery to a new empty Btrfs staging directory, not the running system.
7. Only approve a CAS deletion after reviewing the dry-run and matching confirmation token.
8. To recover a complete UEFI machine, follow the [ReaR guide](RECUPERATION_REAR_FR.md) and test in a disposable VM.

This is an alpha release. See the [certification scope](../VALIDATION.md).
