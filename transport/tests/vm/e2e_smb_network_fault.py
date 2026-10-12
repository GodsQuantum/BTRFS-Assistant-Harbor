#!/usr/bin/env python3
"""Live CIFS/SMB3 disconnection/reconnection validation with disposable QEMU Btrfs guest.

Requires root ONLY inside disposable LXC700 to operate isolated Docker Samba.
Never creates or modifies mounts on the LXC host, Cloud9 or Pegasus.
"""
import hashlib, pathlib, shutil, subprocess, tempfile, time, urllib.request, pexpect
from e2e_alpine_btrfs import extract_iso, ALPINE_VERSION, BIN
BASE=pathlib.Path("/home/arezki/Dev")
SAMBA="harbor-qa-smb-disconnect"
SMB_DIR=BASE/".harbor-disconnect-fixture/smb"
SERVER=["docker","run","-d","--name",SAMBA,"-p","127.0.0.1:445:445",
        "-v",f"{SMB_DIR}:/backup","dperson/samba:latest","-u","lab;harboronly123","-s","backup;/backup;yes;no;no;lab"]
BOOT=r"""#!/bin/sh
set -eu
ip link set eth0 up
udhcpc -i eth0 -q
echo https://dl-cdn.alpinelinux.org/alpine/v3.23/main > /etc/apk/repositories
apk add --no-cache btrfs-progs coreutils cifs-utils attr >/tmp/apk.log
# Host 9p share was mounted during VM bootstrap by the orchestrator.
test -f /mnt/share/harbor-transport
mkdir -p /mnt/smb
mount -t cifs //10.0.2.2/backup /mnt/smb -o username=lab,password=harboronly123,vers=3.0,uid=1000,gid=1000,noperm,file_mode=0777,dir_mode=0777,cache=none,soft,echo_interval=1
grep -qs " /mnt/smb cifs " /proc/mounts
mkdir -p /mnt/smb/cas
cp /mnt/share/harbor-transport /tmp/harbor-transport
chmod 700 /tmp/harbor-transport
adduser -D -u 1000 harborbackup
export PKEXEC_UID=1000
/tmp/harbor-transport init --repo /mnt/smb/cas
mkfs.btrfs -fq /dev/vda
mkdir -p /mnt/fs
mount -t btrfs /dev/vda /mnt/fs
btrfs subvolume create /mnt/fs/work
mkdir -p /mnt/fs/work/docs
echo original > /mnt/fs/work/docs/test.txt
dd if=/dev/urandom of=/mnt/fs/work/payload bs=1M count=8 status=none
sync
btrfs subvolume snapshot -r /mnt/fs/work /mnt/fs/base
/tmp/harbor-transport send --repo /mnt/smb/cas --name base --snapshot /mnt/fs/base --experimental --retries 2
test "$(stat -c %u /mnt/smb/cas/manifests/base.json)" = 1000
echo changed > /mnt/fs/work/docs/test.txt
dd if=/dev/urandom of=/mnt/fs/work/big bs=1M count=64 status=none
sync
btrfs subvolume snapshot -r /mnt/fs/work /mnt/fs/next
echo SMB_BASELINE_OK
"""
RUN=r"""#!/bin/sh
export PKEXEC_UID=1000
timeout 140 /tmp/harbor-transport send --repo /mnt/smb/cas --name next --snapshot /mnt/fs/next --parent /mnt/fs/base --parent-archive base --experimental --retries 7 > /mnt/share/smb-transfer-result.log 2>&1
result=$?
cat /mnt/share/smb-transfer-result.log
if [ "$result" -ne 0 ]; then echo SMB_FAULT_TRANSFER_FAILED_$result; exit "$result"; fi
/tmp/harbor-transport verify-stream --repo /mnt/smb/cas --name next
mkdir -p /mnt/fs/received
/tmp/harbor-transport receive --repo /mnt/smb/cas --name next --staging /mnt/fs/received --confirm
cmp /mnt/fs/work/docs/test.txt /mnt/fs/received/next/docs/test.txt
cmp /mnt/fs/work/big /mnt/fs/received/next/big
test "$(stat -c %u /mnt/smb/cas/manifests/next.json)" = 1000
echo SMB_RECOVERY_DATA_MATCH
"""

MID_PREPARE = r"""#!/bin/sh
set -eu
dd if=/dev/urandom of=/mnt/fs/work/payload-midstream bs=1M count=128 status=none
echo "third version for in-flight stop" > /mnt/fs/work/docs/test.txt
sync
btrfs subvolume snapshot -r /mnt/fs/work /mnt/fs/mid
echo MID_PREPARED
"""

MID_RUN = r"""#!/bin/sh
export PKEXEC_UID=1000
timeout 170 /tmp/harbor-transport send --repo /mnt/smb/cas --name mid --snapshot /mnt/fs/mid --parent /mnt/fs/next --parent-archive next --experimental --retries 7 > /mnt/share/smb-mid-result.log 2>&1
status=$?
cat /mnt/share/smb-mid-result.log
if [ "$status" -ne 0 ]; then echo SMB_MID_FAILED_$status; exit "$status"; fi
/tmp/harbor-transport verify-stream --repo /mnt/smb/cas --name mid
mkdir -p /mnt/fs/mid-received
/tmp/harbor-transport receive --repo /mnt/smb/cas --name mid --staging /mnt/fs/mid-received --confirm
cmp /mnt/fs/work/docs/test.txt /mnt/fs/mid-received/mid/docs/test.txt
cmp /mnt/fs/work/payload-midstream /mnt/fs/mid-received/mid/payload-midstream
test "$(stat -c %u /mnt/smb/cas/manifests/mid.json)" = 1000
echo SMB_MIDSTREAM_RECOVERED_AND_DATA_MATCH
"""

def run_server():
    subprocess.run(["docker","rm","-f",SAMBA],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    subprocess.run(SERVER,check=True,stdout=subprocess.DEVNULL)
    deadline=time.monotonic()+12
    while time.monotonic()<deadline:
        if subprocess.run(["bash","-c","</dev/tcp/127.0.0.1/445"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:
            return
        time.sleep(.2)
    raise RuntimeError("test-only SMB not listening")

def command(child, script, token, timeout):
    child.sendline(("sh /mnt/share/"+script).encode())
    child.expect(token.encode(),timeout=timeout)
    child.expect(b"localhost:~#",timeout=30)
    print("PASS", token, flush=True)

def main():
    assert BIN.exists()
    SMB_DIR.mkdir(parents=True, exist_ok=True)
    # Each guest creates different random snapshot data. Never reuse a
    # previously finalized manifest under the same synthetic archive name.
    # This deletion is scoped strictly to the private laboratory fixture.
    lab_cas = SMB_DIR / "cas"
    if lab_cas.exists():
        assert (lab_cas / ".harbor-repo-id").is_file(), "unexpected non-lab SMB data"
        shutil.rmtree(lab_cas)
    run_server()
    try:
        with tempfile.TemporaryDirectory(dir=BASE,prefix=".harbor-smb-real-") as td:
            p=pathlib.Path(td); share=p/"share";share.mkdir()
            iso=BASE/".harbor-disconnect-fixture/alpine.iso"
            if not iso.exists():
                url=f"https://dl-cdn.alpinelinux.org/alpine/v3.23/releases/x86_64/alpine-virt-{ALPINE_VERSION}-x86_64.iso"
                with urllib.request.urlopen(url,timeout=50) as incoming, iso.open("wb") as outgoing:
                    shutil.copyfileobj(incoming,outgoing)
            extract_iso(iso,p)
            subprocess.run(["truncate","-s","768M",str(p/"disk.raw")],check=True)
            shutil.copy2(BIN,share/"harbor-transport")
            (share/"boot.sh").write_text(BOOT)
            (share/"fault.sh").write_text(RUN)
            (share/"midprep.sh").write_text(MID_PREPARE)
            (share/"midrun.sh").write_text(MID_RUN)
            args=["-machine","q35,accel=tcg","-cpu","qemu64","-m","1024","-smp","2",
                  "-kernel",str(p/"vmlinuz-virt"),"-initrd",str(p/"initramfs-virt"),
                  "-append","console=ttyS0,115200 alpine_dev=sr0","-cdrom",str(iso),
                  "-drive",f"file={p/'disk.raw'},format=raw,if=virtio",
                  "-virtfs",f"local,path={share},security_model=none,mount_tag=hostshare,id=host0",
                  "-netdev","user,id=n0","-device","virtio-net-pci,netdev=n0",
                  "-display","none","-serial","stdio","-monitor","none","-no-reboot"]
            child=pexpect.spawn("qemu-system-x86_64",args,encoding=None,timeout=180)
            with (p/"vm.log").open("wb") as logfile:
                child.logfile=logfile
                try:
                    child.expect(b"localhost login:",timeout=180)
                    child.sendline(b"root")
                    child.expect(b"localhost:~#",timeout=35)
                    child.sendline(b"stty -echo")
                    child.expect(b"localhost:~#",timeout=15)
                    child.sendline(b"mkdir -p /mnt/share; mount -t 9p -o trans=virtio,version=9p2000.L hostshare /mnt/share && echo HOSTSHARE_READY")
                    child.expect(b"HOSTSHARE_READY",timeout=30)
                    child.expect(b"localhost:~#",timeout=15)
                    command(child,"boot.sh","SMB_BASELINE_OK",180)
                    child.sendline(b"echo STARTING_SMB_FAULT; sh /mnt/share/fault.sh; echo SMB_FAULT_RUN_ENDED")
                    child.expect(b"STARTING_SMB_FAULT",timeout=30)
                    print("FAULT: test-only SMB service stopping",flush=True)
                    subprocess.run(["docker","stop","-t","1",SAMBA],check=True,stdout=subprocess.DEVNULL)
                    time.sleep(5)
                    subprocess.run(["docker","start",SAMBA],check=True,stdout=subprocess.DEVNULL)
                    print("FAULT: test-only SMB service restarted",flush=True)
                    finished = child.expect([
                        b"SMB_RECOVERY_DATA_MATCH",
                        b"SMB_FAULT_TRANSFER_FAILED_[0-9]+",
                    ], timeout=170)
                    if finished != 0:
                        raise RuntimeError("CIFS backup failed despite restored SMB service")
                    child.expect(b"SMB_FAULT_RUN_ENDED",timeout=35)
                    if (share/"smb-transfer-result.log").exists():
                        print("BACKUP_RESULT", (share/"smb-transfer-result.log").read_text()[-1000:],flush=True)
                    print("PASS LIVE SMB3 PREFLIGHT OUTAGE RECONNECT RESTORE",flush=True)
                    command(child, "midprep.sh", "MID_PREPARED", 110)
                    # Guarantee that the server is stopped only AFTER actual
                    # compressed CAS objects have been written over SMB.
                    objects = SMB_DIR / "cas" / "objects"
                    initial = len(list(objects.glob("*/*.zst")))
                    child.sendline(b"sh /mnt/share/midrun.sh; echo SMB_MID_RUN_ENDED")
                    deadline = time.monotonic() + 90
                    observed = initial
                    while time.monotonic() < deadline:
                        observed = len(list(objects.glob("*/*.zst")))
                        if observed >= initial + 3:
                            break
                        time.sleep(.2)
                    if observed < initial + 3:
                        raise RuntimeError("No midstream CAS objects observed before interruption")
                    print(f"FAULT: {observed - initial} new compressed objects landed; stopping SMB midstream",flush=True)
                    subprocess.run(["docker","stop","-t","1",SAMBA],check=True,stdout=subprocess.DEVNULL)
                    time.sleep(6)
                    subprocess.run(["docker","start",SAMBA],check=True,stdout=subprocess.DEVNULL)
                    print("FAULT: SMB server restarted during live stream",flush=True)
                    match = child.expect([
                        b"SMB_MIDSTREAM_RECOVERED_AND_DATA_MATCH",
                        b"SMB_MID_FAILED_[0-9]+",
                    ], timeout=200)
                    if match != 0:
                        raise RuntimeError("CAS failed during midstream SMB restart")
                    child.expect(b"SMB_MID_RUN_ENDED",timeout=35)
                    print("PASS LIVE SMB3 IN-FLIGHT OUTAGE RECONNECT RESTORE",flush=True)
                    child.sendline(b"poweroff")
                    child.expect(pexpect.EOF,timeout=45)
                except BaseException:
                    logfile.flush()
                    print("VM LOG TAIL", (p/"vm.log").read_bytes()[-4000:].decode("utf8","replace"),flush=True)
                    raise
                finally:
                    if child.isalive():child.terminate(force=True)
    finally:
        subprocess.run(["docker","rm","-f",SAMBA],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
if __name__=="__main__":
    main()
