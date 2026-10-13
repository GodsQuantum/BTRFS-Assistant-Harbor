#!/usr/bin/env python3
"""Disposable 3-VM NFSv4 kernel lock probe: server + 2 independent clients.

Tests cross-client flock semantics on the same NFSv4.1 export and demonstrates
the effect (if supported by the guest kernel) of local_lock=flock.
No host mounts, no real NAS, no production data, no destructive CAS command.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import subprocess
import tempfile
import time

import pexpect
import e2e_nfs4_kernel_fault as vm
from e2e_alpine_btrfs import EXPECTED_ISO_SHA256
import hashlib

CLIENT_A = r"""#!/bin/sh
set -eu
hostname harbor-lock-a
test "$(hostname)" = harbor-lock-a
grep -q 'nfs.nfs4_unique_id=harbor-lock-a' /proc/cmdline
ip link set eth0 up
udhcpc -i eth0 -q
echo https://dl-cdn.alpinelinux.org/alpine/v3.23/main > /etc/apk/repositories
apk add --no-cache nfs-utils util-linux coreutils >/tmp/apk.log 2>&1 || { cat /tmp/apk.log; exit 71; }
echo PACKAGES_READY
command -v flock
mkdir -p /mnt/nfs
timeout 45 mount -t nfs4 -o vers=4.1,proto=tcp,port=2050,soft,timeo=10,retrans=2 10.0.2.2:/ /mnt/nfs || { echo NFS_MOUNT_FAILED; exit 72; }
echo NFS_MOUNT_READY
mkdir -p /mnt/nfs/cas
: > /mnt/nfs/cas/.lock-probe
flock -x -n /tmp/harbor-local-lock -c true || { echo LOCAL_FLOCK_BROKEN; exit 76; }
echo LOCAL_FLOCK_COMMAND_READY
(flock -x -w 15 /mnt/nfs/cas/.lock-probe -c 'echo HELD > /mnt/share/lock-held; while [ ! -f /mnt/share/lock-release ]; do sleep 1; done' || echo NFS_FLOCK_FAILED_RC:$?) &
echo $! > /mnt/share/locker.pid
i=0
while [ "$i" -lt 120 ] && [ ! -f /mnt/share/lock-held ]; do
    sleep 0.2
    i=$((i + 1))
done
test -f /mnt/share/lock-held || { echo LOCK_WAIT_TIMEOUT; cat /proc/locks | tail -12; exit 74; }
kill -0 "$(cat /mnt/share/locker.pid)" || { echo LOCK_OWNER_DIED; exit 75; }
if flock -x -n /mnt/nfs/cas/.lock-probe -c true; then
    echo UNSAFE_SAME_CLIENT_LOCK_REACQUIRED
    exit 77
fi
echo NFS4_CLIENT_A_LOCK_HELD
"""
CLIENT_B = r"""#!/bin/sh
set -eu
hostname harbor-lock-b
test "$(hostname)" = harbor-lock-b
grep -q 'nfs.nfs4_unique_id=harbor-lock-b' /proc/cmdline
ip link set eth0 up
udhcpc -i eth0 -q
echo https://dl-cdn.alpinelinux.org/alpine/v3.23/main > /etc/apk/repositories
apk add --no-cache nfs-utils util-linux coreutils >/tmp/apk.log 2>&1 || { cat /tmp/apk.log; exit 71; }
echo PACKAGES_READY
command -v flock
mkdir -p /mnt/nfs
timeout 45 mount -t nfs4 -o vers=4.1,proto=tcp,port=2050,soft,timeo=10,retrans=2 10.0.2.2:/ /mnt/nfs || { echo NFS_MOUNT_FAILED; exit 72; }
echo NFS_MOUNT_READY
test -f /mnt/nfs/cas/.lock-probe
if flock -x -n /mnt/nfs/cas/.lock-probe -c true; then
   echo UNSAFE_SECOND_CLIENT_TAKES_FIRST_CLIENT_LOCK
fi
echo NFS4_CROSS_CLIENT_LOCK_EXCLUSION_VERIFIED
mkdir -p /mnt/nfs-unsafe
if timeout 30 mount -t nfs4 -o vers=4.1,proto=tcp,port=2050,soft,timeo=10,retrans=2,local_lock=flock 10.0.2.2:/ /mnt/nfs-unsafe; then
    if flock -x -n /mnt/nfs-unsafe/cas/.lock-probe -c true; then
        echo UNSAFE_LOCAL_LOCK_OPTION_BYPASSES_INTERCLIENT_LOCK
    else
        echo LOCAL_LOCK_OPTION_PRESENT_BUT_BYPASS_NOT_REPRODUCED
    fi
else
    echo LOCAL_LOCK_OPTION_MOUNT_UNSUPPORTED
fi
echo NFS4_LOCK_VARIANT_TEST_COMPLETE
"""

def named_guest_command(child: pexpect.spawn, script: str, ready: str,
                        hostname: str, timeout: int = 170) -> None:
    # Changing UTS hostname is essential to unique NFSv4 client identity;
    # Alpine updates its shell prompt immediately, so a fixed localhost
    # prompt would time out after the test script actually succeeded.
    child.sendline(f"sh /mnt/share/{script}; echo GUEST_COMMAND_RETURNED".encode())
    index = child.expect([ready.encode(), b"GUEST_COMMAND_RETURNED"], timeout=timeout)
    if index != 0:
        raise RuntimeError(f"guest {hostname} script failed before {ready}")
    child.expect(b"GUEST_COMMAND_RETURNED", timeout=30)
    child.expect(f"{hostname}:~#".encode(), timeout=20)
    print("PASS", ready, flush=True)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iso", type=Path, required=True)
    args = parser.parse_args()
    assert hashlib.sha256(args.iso.read_bytes()).hexdigest() == EXPECTED_ISO_SHA256
    with tempfile.TemporaryDirectory(prefix=".harbor-nfs-lock-qa-", dir=Path("/home/arezki/Dev")) as tmp:
        base=Path(tmp)
        s,a,b=[base/x for x in ("server","client-a","client-b")]
        for folder in (s,a,b):
            folder.mkdir()
            (folder/"share").mkdir()
        (s/"share/server.sh").write_text(vm.SERVER_SCRIPT)
        (a/"share/boot.sh").write_text(CLIENT_A)
        (b/"share/boot.sh").write_text(CLIENT_B)
        children=[]
        with (base/"server-console.log").open("wb") as sf, (base/"a-console.log").open("wb") as af, (base/"b-console.log").open("wb") as bf:
            try:
                server=vm.start_guest(vm.make_guest(s,args.iso,",hostfwd=tcp:127.0.0.1:2050-:2049",ram=768),sf)
                children.append(server)
                vm.guest_command(server,"server.sh","KERNEL_NFSV4_SERVER_READY",160)
                a_args=vm.make_guest(a,args.iso,"",with_disk=False,ram=512)
                a_args[a_args.index("-append")+1] += " nfs.nfs4_unique_id=harbor-lock-a"
                ca=vm.start_guest(a_args,af)
                children.append(ca)
                named_guest_command(ca,"boot.sh","NFS4_CLIENT_A_LOCK_HELD","harbor-lock-a",160)
                b_args=vm.make_guest(b,args.iso,"",with_disk=False,ram=512)
                b_args[b_args.index("-append")+1] += " nfs.nfs4_unique_id=harbor-lock-b"
                cb=vm.start_guest(b_args,bf)
                children.append(cb)
                named_guest_command(cb,"boot.sh","NFS4_LOCK_VARIANT_TEST_COMPLETE","harbor-lock-b",160)
                # Ensure A's holder is still alive AFTER the second guest's
                # full boot/package install; otherwise a time-limited holder
                # would yield a false inter-client locking failure.
                ca.sendline(b'kill -0 "$(cat /mnt/share/locker.pid)" && ! flock -x -n /mnt/nfs/cas/.lock-probe -c true && echo NFS4_A_LOCK_STILL_ACTIVE')
                ca.expect(b'NFS4_A_LOCK_STILL_ACTIVE',timeout=20)
                ca.expect(b'harbor-lock-a:~#',timeout=20)
                bf.flush()
                client_b_log=(base/"b-console.log").read_bytes().decode("utf-8","replace")
                if "UNSAFE_SECOND_CLIENT_TAKES_FIRST_CLIENT_LOCK" in client_b_log:
                    raise RuntimeError("second NFS4 client incorrectly acquired an exclusive lock")
                if "NFS4_CROSS_CLIENT_LOCK_EXCLUSION_VERIFIED" not in client_b_log:
                    raise RuntimeError("NFS4 cross-client lock exclusion not proven")
                if "UNSAFE_LOCAL_LOCK_OPTION_BYPASSES_INTERCLIENT_LOCK" in client_b_log:
                    print("PASS UNSAFE NFS local_lock=flock DEMONSTRATED",flush=True)
                elif "LOCAL_LOCK_OPTION_PRESENT_BUT_BYPASS_NOT_REPRODUCED" in client_b_log:
                    print("INCONCLUSIVE NFS local_lock override did not bypass in this VM",flush=True)
                else:
                    print("INCONCLUSIVE NFS local_lock mount unsupported in this guest",flush=True)
                print("PASS NFSV4 CROSS-CLIENT flock EXCLUSION (2 distinct clients)",flush=True)
            except BaseException:
                for label, path in (("SERVER",s/"server-console.log"),("CLIENT_A",a/"share"/"lock-held"),("CLIENT_B",b/"b-console.log")):
                    if path.is_file():
                        print(label, path.read_bytes()[-2400:].decode("utf8","replace"),flush=True)
                for label, logfile in (("A",base/"a-console.log"),("B",base/"b-console.log")):
                    if logfile.exists(): print(label,logfile.read_bytes()[-3000:].decode("utf8","replace"),flush=True)
                raise
            finally:
                for child in reversed(children):
                    if child.isalive():
                        child.terminate(force=True)

if __name__ == "__main__":
    main()
