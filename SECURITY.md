# Security policy 🛡️

**Supported:** latest stable Linux x86-64 release and active development branch; see [Releases](https://github.com/GodsQuantum/BTRFS-Assistant-Harbor/releases/latest).

For vulnerabilities, use GitHub [Security Advisories / private vulnerability reporting](https://github.com/GodsQuantum/BTRFS-Assistant-Harbor/security/advisories) where enabled. **Never publish an exploitable payload, credentials, user backup contents, or private keys in a public issue.**

Security boundaries:

- Snapshot paths and archive names are untrusted inputs and must not be interpreted as shell commands.
- Validate the live NFS/SMB mount before writing; reject local fallbacks.
- CAS pruning requires current preview and plan digest; destructive GC on NFS/SMB/SSHFS/9p is deliberately unsupported.
- Restore into a new empty Btrfs staging target, never overwrite the running root.
- ReaR recovery is not certified for Secure Boot, LUKS/LVM/RAID or multiple Btrfs roots.
- Keep secrets out of manifests, tests, CI logs and documentation.

There is no guaranteed security response SLA.
