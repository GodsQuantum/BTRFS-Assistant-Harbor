#!/usr/bin/env python3
"""Isolated NFSv4.1 kernel server + Linux NFS client, disposable QEMU TCG.

No mounts/export changes on Cloud9, LXC700 host or Pegasus. Both server
and client run in unprivileged disposable guest VMs, with separate disks.
Pauses the SERVER VM during active NFS writes to prove restart/resume.
"""
import os
import pathlib
import shutil
import signal
import subprocess
import tempfile
import time
import pexpect
from e2e_alpine_btrfs import extract_iso, BIN

LAB = pathlib.Path('/home/arezki/Dev/.harbor-nfs3-lab')
ISO = LAB / 'alpine.iso'
ROOT = pathlib.Path('/home/arezki/Dev')

SERVER_SCRIPT = r"""#!/bin/sh
set -eu
ip link set eth0 up
udhcpc -i eth0 -q
echo https://dl-cdn.alpinelinux.org/alpine/v3.23/main > /etc/apk/repositories
apk add --no-cache nfs-utils e2fsprogs coreutils >/tmp/apk.log
modprobe nfsd
modprobe ext4
mkfs.ext4 -q -F /dev/vda
mkdir -p /srv/test-export
mount -t ext4 /dev/vda /srv/test-export
chown 1000:1000 /srv/test-export
chmod 0777 /srv/test-export
mkdir -p /proc/fs/nfsd
mount -t nfsd nfsd /proc/fs/nfsd
echo '/srv/test-export *(rw,sync,fsid=0,no_subtree_check,no_root_squash,insecure)' > /etc/exports
rpcbind -w
exportfs -rav
rpc.mountd
rpc.nfsd 2
grep -q '+4.1' /proc/fs/nfsd/versions
test "$(cat /proc/fs/nfsd/threads)" = 2
(
 while :; do
  find /srv/test-export/cas/objects -type f -name '*.zst' 2>/dev/null | wc -l > /mnt/share/object-count.txt
  sleep 0.2
 done
) >/tmp/count.log 2>&1 &
echo KERNEL_NFSV4_SERVER_READY
"""

CLIENT_BOOT = r"""#!/bin/sh
set -eu
ip link set eth0 up
udhcpc -i eth0 -q
echo https://dl-cdn.alpinelinux.org/alpine/v3.23/main > /etc/apk/repositories
apk add --no-cache btrfs-progs nfs-utils coreutils iproute2 >/tmp/apk.log
mkdir -p /mnt/nfs
timeout 45 mount -t nfs4 -o vers=4.1,proto=tcp,port=2050,soft,timeo=10,retrans=2 10.0.2.2:/ /mnt/nfs
grep -qs ' /mnt/nfs nfs4 ' /proc/mounts
mkdir -p /mnt/nfs/cas
chown 1000:1000 /mnt/nfs/cas
cp /mnt/share/harbor-transport /tmp/harbor-transport
chmod 700 /tmp/harbor-transport
adduser -D -u 1000 harborbackup
export PKEXEC_UID=1000
/tmp/harbor-transport init --repo /mnt/nfs/cas
test "$(stat -c %u /mnt/nfs/cas/.harbor-repo-id)" = 1000
mkfs.btrfs -fq /dev/vda
mkdir -p /mnt/fs
mount -t btrfs /dev/vda /mnt/fs
btrfs subvolume create /mnt/fs/work
mkdir -p /mnt/fs/work/docs
echo original > /mnt/fs/work/docs/test.txt
dd if=/dev/urandom of=/mnt/fs/work/data bs=1M count=12 status=none
sync
btrfs subvolume snapshot -r /mnt/fs/work /mnt/fs/base
/tmp/harbor-transport send --repo /mnt/nfs/cas --name base --snapshot /mnt/fs/base --experimental --retries 2
echo second > /mnt/fs/work/docs/test.txt
sync
btrfs subvolume snapshot -r /mnt/fs/work /mnt/fs/next
/tmp/harbor-transport send --repo /mnt/nfs/cas --name next --snapshot /mnt/fs/next --parent /mnt/fs/base --parent-archive base --experimental --retries 2
/tmp/harbor-transport verify-stream --repo /mnt/nfs/cas --name next
mkdir -p /mnt/fs/received
/tmp/harbor-transport receive --repo /mnt/nfs/cas --name next --staging /mnt/fs/received --confirm
cmp /mnt/fs/work/docs/test.txt /mnt/fs/received/next/docs/test.txt
echo NFS4_BASELINE_VERIFIED
"""

CLIENT_MID = r"""#!/bin/sh
set -eu
export PKEXEC_UID=1000
dd if=/dev/urandom of=/mnt/fs/work/mid-data bs=1M count=112 status=none
echo updated > /mnt/fs/work/docs/test.txt
sync
btrfs subvolume snapshot -r /mnt/fs/work /mnt/fs/mid
echo NFS4_MID_READY
set +e
timeout 230 /tmp/harbor-transport send --repo /mnt/nfs/cas --name mid --snapshot /mnt/fs/mid --parent /mnt/fs/next --parent-archive next --experimental --retries 8 > /mnt/share/nfs4-result.log 2>&1
rc=$?
set -e
cat /mnt/share/nfs4-result.log
test "$rc" = 0 || { echo NFS4_MID_SEND_FAILED; exit "$rc"; }
/tmp/harbor-transport verify-stream --repo /mnt/nfs/cas --name mid
mkdir -p /mnt/fs/received2
/tmp/harbor-transport receive --repo /mnt/nfs/cas --name mid --staging /mnt/fs/received2 --confirm
cmp /mnt/fs/work/docs/test.txt /mnt/fs/received2/mid/docs/test.txt
cmp /mnt/fs/work/mid-data /mnt/fs/received2/mid/mid-data
echo NFS4_MID_RESTORED_EXACTLY
"""

CLIENT_FALLBACK = r"""#!/bin/sh
set -eu
cp /mnt/nfs/cas/.harbor-repo-id /tmp/repo-id
umount /mnt/nfs
mkdir -p /mnt/nfs/cas/manifests /mnt/nfs/cas/objects
cp /tmp/repo-id /mnt/nfs/cas/.harbor-repo-id
if /tmp/harbor-transport send --repo /mnt/nfs/cas --name illegal-local --snapshot /mnt/fs/base --experimental --retries 0; then
 echo UNSAFE_LOCAL_WRITE
 exit 34
fi
test ! -e /mnt/nfs/cas/manifests/illegal-local.json
echo NFS4_OFFLINE_FALLBACK_REFUSED
"""

def make_guest(root, iso, extra, with_disk=True, ram=768):
    root.mkdir(exist_ok=True)
    extract_iso(iso, root)
    args=['-machine','q35,accel=tcg','-cpu','qemu64','-m',str(ram),'-smp','1',
          '-kernel',str(root/'vmlinuz-virt'),'-initrd',str(root/'initramfs-virt'),
          '-append','console=ttyS0,115200 alpine_dev=sr0','-cdrom',str(iso)]
    if with_disk:
        subprocess.run(['truncate','-s','768M',str(root/'disk.raw')],check=True)
        args+=['-drive',f'file={root/"disk.raw"},format=raw,if=virtio']
    args+=['-virtfs',f'local,path={root/"share"},security_model=none,mount_tag=hostshare,id=host0']
    args+=['-netdev','user,id=n0'+extra,'-device','virtio-net-pci,netdev=n0',
           '-display','none','-serial','stdio','-monitor','none','-no-reboot']
    return args

def start_guest(args, output):
    child=pexpect.spawn('qemu-system-x86_64',args,encoding=None,timeout=180)
    child.logfile=output
    child.expect(b'localhost login:',timeout=180)
    child.sendline(b'root')
    child.expect(b'localhost:~#',timeout=30)
    child.sendline(b'stty -echo')
    child.expect(b'localhost:~#',timeout=20)
    child.sendline(b'mkdir -p /mnt/share; mount -t 9p -o trans=virtio,version=9p2000.L hostshare /mnt/share && echo SHARE_READY')
    child.expect(b'SHARE_READY',timeout=35)
    child.expect(b'localhost:~#',timeout=20)
    return child

def guest_command(child, script, ready, timeout):
    child.sendline(('sh /mnt/share/'+script+'; echo GUEST_COMMAND_RETURNED').encode())
    outcome = child.expect([ready.encode(), b'GUEST_COMMAND_RETURNED'], timeout=timeout)
    if outcome != 0:
        raise RuntimeError('guest script failed before expected success: ' + ready)
    child.expect(b'GUEST_COMMAND_RETURNED',timeout=30)
    child.expect(b'localhost:~#',timeout=20)
    print('PASS',ready,flush=True)

def count_objects(path):
    try:
        return int(path.read_text().strip())
    except (ValueError,OSError):
        return 0

def main():
    assert BIN.is_file() and ISO.is_file()
    with tempfile.TemporaryDirectory(prefix='.harbor-kernel-nfs4-',dir=ROOT) as tmp:
        base=pathlib.Path(tmp)
        s=base/'server'; c=base/'client'; s.mkdir(); c.mkdir()
        (s/'share').mkdir(); (c/'share').mkdir()
        shutil.copy2(BIN,c/'share/harbor-transport')
        (s/'share/server.sh').write_text(SERVER_SCRIPT)
        (c/'share/boot.sh').write_text(CLIENT_BOOT)
        (c/'share/mid.sh').write_text(CLIENT_MID)
        (c/'share/fallback.sh').write_text(CLIENT_FALLBACK)
        server=None;client=None;paused=False
        with (base/'server-console.log').open('wb') as sf, (base/'client-console.log').open('wb') as cf:
            try:
                server=start_guest(make_guest(s,ISO,',hostfwd=tcp:127.0.0.1:2050-:2049',ram=768),sf)
                guest_command(server,'server.sh','KERNEL_NFSV4_SERVER_READY',160)
                client=start_guest(make_guest(c,ISO,'',ram=1024),cf)
                guest_command(client,'boot.sh','NFS4_BASELINE_VERIFIED',220)
                print('PASS REAL KERNEL NFSV4 FULL AND INCREMENTAL BTRFS',flush=True)
                client.sendline(b'modprobe sch_tbf || :; tc qdisc replace dev eth0 root tbf rate 25mbit burst 128kb latency 500ms && echo THROTTLED')
                client.expect(b'THROTTLED',timeout=35)
                client.expect(b'localhost:~#',timeout=20)
                before=count_objects(s/'share/object-count.txt')
                client.sendline(b'sh /mnt/share/mid.sh; echo MID_SCRIPT_END')
                client.expect(b'NFS4_MID_READY',timeout=130)
                deadline=time.monotonic()+90
                after=before
                while time.monotonic()<deadline:
                    after=count_objects(s/'share/object-count.txt')
                    if after >= before+3:break
                    time.sleep(0.2)
                if after < before+3:
                    raise RuntimeError('kernel NFSv4 server did not persist 3 new objects before fault')
                os.kill(server.pid,signal.SIGSTOP)
                paused=True
                print('FAULT KERNEL NFS4 SERVER VM FROZEN AFTER',after-before,'OBJECTS',flush=True)
                time.sleep(6)
                os.kill(server.pid,signal.SIGCONT)
                paused=False
                print('FAULT KERNEL NFS4 SERVER RESUMED',flush=True)
                client.expect(b'NFS4_MID_RESTORED_EXACTLY',timeout=210)
                client.expect(b'MID_SCRIPT_END',timeout=40)
                client.expect(b'localhost:~#',timeout=20)
                print('PASS KERNEL NFS4 LIVE PAUSE RETRY NATIVE RESTORE',flush=True)
                guest_command(client,'fallback.sh','NFS4_OFFLINE_FALLBACK_REFUSED',70)
                print('PASS NFS4 MOUNT IDENTITY SAFETY',flush=True)
                client.sendline(b'poweroff')
                client.expect(pexpect.EOF,timeout=45)
                server.sendline(b'poweroff')
                server.expect(pexpect.EOF,timeout=45)
            except BaseException:
                sf.flush();cf.flush()
                for label, logfile in [('SERVER',base/'server-console.log'),('CLIENT',base/'client-console.log')]:
                    print(label+'_LOG',logfile.read_bytes()[-3500:].decode('utf8','replace'),flush=True)
                raise
            finally:
                if paused and server is not None:
                    os.kill(server.pid,signal.SIGCONT)
                for guest in (client,server):
                    if guest is not None and guest.isalive():guest.terminate(force=True)
if __name__=='__main__':
    main()
