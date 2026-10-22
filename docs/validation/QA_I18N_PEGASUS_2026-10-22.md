# Harbor 0.1.2 — EN/FR/中文 UI and Pegasus staged without backup

## Product scope
- Three visible language choices in Qt: English, Français, 简体中文.
- Store preference ui/language with machine name cas/machineName, remote/engine and remote/targetPath in the existing BtrfsAssistantHarbor/Harbor QSettings.
- The explicit selection survives a root GUI started through pkexec with the C/POSIX locale. Reopen the app (not the computer) to translate every control consistently.
- Qt6 lupdate must find zero missing or unfinished active messages in all src code for French and Simplified Chinese, and no mismatched Qt parameter placeholders. QTest checks actual .qm files, native option names, root/C locale fallback and persistence.

## Pegasus scope
- Keep the existing NFS mount /mnt/Cloud9/backup-local/Workstations/ and its one shared CAS object pool.
- Use machine identity Pegasus, manifest location Workstations/machines/Pegasus/manifests/, global Workstations/objects/. Do not create Workstations/Pegasus as a separate CAS repository, nor alter old existing directories.
- Use saved language fr_FR, remote/engine cas and existing shared targetPath. Do not create or enable a timer or a service, send a backup, trigger Snapper snapshots or touch the spring cleaning.
- A first real backup requires a new explicit green light from the user.

## Release gate
Do not publish a new stable build until 11/11 CI jobs succeed on that revision, the three published package hashes verify, and Pegasus package and settings checks pass. macOS/APFS is not implemented, while network destructive CAS GC remains refused.
