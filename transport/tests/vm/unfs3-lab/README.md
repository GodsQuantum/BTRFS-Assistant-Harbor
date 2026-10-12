# Disposable NFSv3 test server

Source: https://github.com/unfs3/unfs3 . The lab Dockerfile builds from
a separately fetched unfs3 source checkout. The test binds ONLY to LXC700
loopback ports 2049 and 20048, and a disposable local export directory.
The client is an Alpine QEMU guest. Production mounts are not affected.

The e2e_nfs3_unfs3_fault.py script freezes this container after three
remote Btrfs objects arrive, resumes, validates the send/receive and
checks that the client refuses fallback writes on NFS unmount.
Never enable the test-only no_root_squash export in production.
