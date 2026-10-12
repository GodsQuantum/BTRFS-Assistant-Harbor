# Arch Linux / CachyOS package (experimental)

This package is a local development build, not an official Arch repository
package. It does not replace the system btrfs-assistant executable or desktop
entry. It installs fork-prefixed GUI files, a separate harbor-checkpoint-v2
legacy Python compatibility backend and the Rust harbor-transport binary.
No services are enabled on installation.

The source is a tracked Git archive and PKGBUILD.in with its SHA256 pinned.
Build in a disposable Arch container and run tests first. Install with
pacman -U only after production NFS/SMB resilience and restoration tests pass,
and with no existing backup in progress.
