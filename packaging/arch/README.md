# Arch Linux / CachyOS package (experimental)

This package is a local development build, not an official Arch repository
package. It does not replace the system btrfs-assistant executable or desktop
entry. It installs fork-prefixed GUI files, a separate harbor-checkpoint-v2
legacy Python compatibility backend and the Rust harbor-transport binary.
Only the read-only progress observer is enabled on installation; no backup is automatically started. The systray also checks live whole-machine systemd units when the observer is unavailable.

The source is a tracked Git archive and PKGBUILD.in with its SHA256 pinned.
Build in a disposable Arch container and run tests first. Install with
pacman -U only after production NFS/SMB resilience and restoration tests pass,
and with no existing backup in progress.

GUI and tray ship the new circular Harbor mark in hicolor PNG sizes.
