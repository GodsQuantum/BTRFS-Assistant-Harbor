# Shared CAS multimachine — alpha9 QA

All workstations select only the parent `Workstations/` destination. There is one repository and one FastCDC/BLAKE3 `objects/` pool for cross-machine deduplication, never a CAS repository per machine.

Structure: `.harbor-repo-id`, `.harbor-repo.lock`, `objects/<prefix>/<blake3>.zst`, `manifests/` (legacy), `machines/Pegasus/manifests/*.json`, `machines/Galactica/manifests/*.json`.

Machine IDs use `m@Machine@Archive`, with `@` forbidden in old archive IDs, ensuring legacy names remain disjoint. Qt automatically detects the Linux hostname and lets the user edit it. CLI `send --repo /Workstations --machine Pegasus --name <archive> --snapshot <readonly-Btrfs-snapshot> --experimental` targets the shared CAS root; manifest is written under `machines/Pegasus/manifests/`. Archive names include config, Snapper number, UTC timestamp and UUID. Independently managed machine profile timers use schema 3; older CAS profile schema 2 still loads.

GC enumerates every machine and legacy manifest under a repository-wide lock, validates retained Btrfs incremental dependency graphs, checks every retained chunk and removes only truly orphaned chunks. Cross-machine incremental parent archives are rejected. Destructive GC on NFS/SMB/SSHFS/9p remains **disabled** pending certification of distributed inter-client locking. Do not bypass this gate.

Galactica/macOS is NOT a native Btrfs computer. An APFS/filesystem capture plugin and portable restore format can use the same CAS in a future version, but are not implemented or certified now. A synthetic QA Galactica identity is not a physical/macOS backup.

QA: Rust multimachine tests, Python schedule tests and actual release CLI `tests/qa_multimachine_cli.py` on isolated ephemeral data (Pegasus 3 chunks new, Galactica 0 new/3 reused, Pegasus updated stream 2 reused; global GC 1 orphan removed, Galactica verified/recovered with equal SHA-256). These do not prove genuine Btrfs send from two physical computers, distributed GC, full Qt Plasma Wayland or cross-OS restore. Remaining release gates G09/G10/G20/G22/G23 MUST pass before a stable/production label. No production machine was modified.
