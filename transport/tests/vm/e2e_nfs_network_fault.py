#!/usr/bin/env python3
"""True NFSv4 Linux mount, NFS-Ganesha MEM FSAL Docker pause and restore.

The server lives in disposable Docker, and Alpine QEMU owns every mount.
No changes to host NFS exports, mount flags or production volumes.
"""
import pathlib, subprocess, tempfile, time, shutil
import pexpect
from e2e_alpine_btrfs import extract_iso, BIN
BASE = pathlib.Path('/home/arezki/Dev')
ISO = BASE / '.harbor-disconnect-fixture/alpine.iso'
SERVER = 'harbor-qa-nfsv4-pause'
NFS_IMAGE = 'harbor-nfs-lab:20261012'

BOOT = r"""#!/bin/sh
set -eu
ip link set eth0 up
udhcpc -i eth0 -q
echo https://dl-cdn.alpinelinux.org/alpine/v3.23/main > /etc/apk/repositories
apk add --no-cache btrfs-progs coreutils nfs-utils attr >/tmp/apk.log
mkdir -p /mnt/nfs
timeout 45 mount -t nfs4 -o vers=4.1,proto=tcp,port=2049,soft,timeo=10,retrans=2 10.0.2.2:/backup /mnt/nfs
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
echo first > /mnt/fs/work/docs/test.txt
dd if=/dev/urandom of=/mnt/fs/work/data bs=1M count=12 status=none
sync
btrfs subvolume snapshot -r /mnt/fs/work /mnt/fs/base
/tmp/harbor-transport send --repo /mnt/nfs/cas --name base --snapshot /mnt/fs/base --experimental --retries 2
test "$(stat -c %u /mnt/nfs/cas/manifests/base.json)" = 1000
echo second > /mnt/fs/work/docs/test.txt
sync
btrfs subvolume snapshot -r /mnt/fs/work /mnt/fs/next
/tmp/harbor-transport send --repo /mnt/nfs/cas --name next --snapshot /mnt/fs/next --parent /mnt/fs/base --parent-archive base --experimental --retries 2
/tmp/harbor-transport verify-stream --repo /mnt/nfs/cas --name next
mkdir -p /mnt/fs/recv
/tmp/harbor-transport receive --repo /mnt/nfs/cas --name next --staging /mnt/fs/recv --confirm
cmp /mnt/fs/work/docs/test.txt /mnt/fs/recv/next/docs/test.txt
echo NFS4_BASELINE_OK
"""

MID = r"""#!/bin/sh
set -eu
export PKEXEC_UID=1000
dd if=/dev/urandom of=/mnt/fs/work/mid-data bs=1M count=112 status=none
echo third > /mnt/fs/work/docs/test.txt
sync
btrfs subvolume snapshot -r /mnt/fs/work /mnt/fs/mid
echo NFS_MID_SNAPSHOT_READY
set +e
timeout 170 /tmp/harbor-transport send --repo /mnt/nfs/cas --name mid --snapshot /mnt/fs/mid --parent /mnt/fs/next --parent-archive next --experimental --retries 7 > /mnt/share/nfs-mid-result.log 2>&1
result=$?
set -e
cat /mnt/share/nfs-mid-result.log
if [ "$result" -ne 0 ]; then
    # Fail closed: transient NFS errors must never create a visible archive.
    if [ -e /mnt/nfs/cas/manifests/mid.json ]; then
        echo UNSAFE_NFS_MANIFEST_COMMITTED_ON_FAILED_UPLOAD
        exit 85
    fi
    echo NFS_UPLOAD_REFUSED_WITHOUT_MANIFEST
else
    # A completed send MUST reverify actual remote bytes.
    /tmp/harbor-transport verify-stream --repo /mnt/nfs/cas --name mid || {
        echo UNSAFE_NFS_COMPLETED_MANIFEST_CORRUPT
        exit 86
    }
    mkdir -p /mnt/fs/recv2
    /tmp/harbor-transport receive --repo /mnt/nfs/cas --name mid --staging /mnt/fs/recv2 --confirm
    cmp /mnt/fs/work/docs/test.txt /mnt/fs/recv2/mid/docs/test.txt
    cmp /mnt/fs/work/mid-data /mnt/fs/recv2/mid/mid-data
    echo NFS_MIDSTREAM_DATA_MATCH
fi
"""

FALLBACK = r"""#!/bin/sh
set -eu
cp /mnt/nfs/cas/.harbor-repo-id /tmp/repo.id
umount /mnt/nfs
mkdir -p /mnt/nfs/cas/manifests /mnt/nfs/cas/objects
cp /tmp/repo.id /mnt/nfs/cas/.harbor-repo-id
if /tmp/harbor-transport send --repo /mnt/nfs/cas --name bad-local    --snapshot /mnt/fs/base --experimental --retries 0; then
    echo BAD_WROTE_TO_UNMOUNTED_FALLBACK
    exit 33
fi
test ! -e /mnt/nfs/cas/manifests/bad-local.json
echo NFS_UNMOUNT_FALLBACK_REFUSED
"""

def docker(*arguments, check=True):
    return subprocess.run(['docker',*arguments],check=check,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
def marker(child, name, timeout):
    child.expect(name.encode(), timeout=timeout)
    child.expect(b'localhost:~#',timeout=30)
    print('PASS',name,flush=True)
def main():
    assert BIN.exists() and ISO.exists()
    docker('rm','-f',SERVER,check=False)
    docker('run','-d','--name',SERVER,'--cpus=1','--memory=512m','-p','127.0.0.1:2049:2049',NFS_IMAGE)
    try:
        with tempfile.TemporaryDirectory(prefix='.harbor-nfs-real-',dir=BASE) as dirname:
            w=pathlib.Path(dirname);share=w/'share';share.mkdir()
            extract_iso(ISO,w)
            subprocess.run(['truncate','-s','768M',str(w/'disk.raw')],check=True)
            shutil.copy2(BIN,share/'harbor-transport')
            (share/'boot.sh').write_text(BOOT)
            (share/'mid.sh').write_text(MID)
            (share/'fallback.sh').write_text(FALLBACK)
            args=['-machine','q35,accel=tcg','-cpu','qemu64','-m','1024','-smp','2',
                  '-kernel',str(w/'vmlinuz-virt'),'-initrd',str(w/'initramfs-virt'),
                  '-append','console=ttyS0,115200 alpine_dev=sr0','-cdrom',str(ISO),
                  '-drive',f'file={w/"disk.raw"},format=raw,if=virtio',
                  '-virtfs',f'local,path={share},security_model=none,mount_tag=hostshare,id=host0',
                  '-netdev','user,id=n0','-device','virtio-net-pci,netdev=n0',
                  '-display','none','-serial','stdio','-monitor','none','-no-reboot']
            child=pexpect.spawn('qemu-system-x86_64',args,encoding=None,timeout=190)
            with (w/'vm.log').open('wb') as logfile:
                child.logfile=logfile
                try:
                    child.expect(b'localhost login:',timeout=190)
                    child.sendline(b'root')
                    child.expect(b'localhost:~#',timeout=30)
                    child.sendline(b'stty -echo')
                    child.expect(b'localhost:~#')
                    child.sendline(b'mkdir -p /mnt/share; mount -t 9p -o trans=virtio,version=9p2000.L hostshare /mnt/share && echo SHARE_READY')
                    child.expect(b'SHARE_READY',timeout=35)
                    child.expect(b'localhost:~#')
                    child.sendline(b'sh /mnt/share/boot.sh')
                    marker(child,'NFS4_BASELINE_OK',175)
                    child.sendline(b'sh /mnt/share/mid.sh; echo NFS_MID_GUEST_FINISHED')
                    child.expect(b'At subvol /mnt/fs/mid',timeout=130)
                    time.sleep(.6)
                    docker('pause',SERVER)
                    print('FAULT paused NFSv4 userspace server during active send',flush=True)
                    time.sleep(8)
                    docker('unpause',SERVER)
                    print('FAULT resumed NFSv4 server',flush=True)
                    found=child.expect([
                        b'NFS_MIDSTREAM_DATA_MATCH',
                        b'NFS_UPLOAD_REFUSED_WITHOUT_MANIFEST',
                        b'UNSAFE_NFS_MANIFEST_COMMITTED_ON_FAILED_UPLOAD',
                        b'UNSAFE_NFS_COMPLETED_MANIFEST_CORRUPT',
                    ],timeout=190)
                    if found >= 2:
                        raise RuntimeError('unsafe remote NFS state: corrupted archive was committed')
                    child.expect(b'NFS_MID_GUEST_FINISHED',timeout=35)
                    if found == 0:
                        print('PASS NFS4 INFLIGHT PAUSE RESUME BTRFS RESTORE',flush=True)
                    else:
                        print('PASS NFS4 FAIL-CLOSED: no damaged manifest committed (resume NOT certified)',flush=True)
                    child.sendline(b'sh /mnt/share/fallback.sh')
                    marker(child,'NFS_UNMOUNT_FALLBACK_REFUSED',55)
                    child.sendline(b'poweroff')
                    child.expect(pexpect.EOF,timeout=45)
                except BaseException:
                    logfile.flush()
                    print('GUEST_LOG_TAIL', (w/'vm.log').read_bytes()[-4500:].decode('utf8','replace'),flush=True)
                    raise
                finally:
                    if child.isalive(): child.terminate(force=True)
    finally:
        docker('unpause',SERVER,check=False)
        docker('rm','-f',SERVER,check=False)
if __name__=='__main__':main()
