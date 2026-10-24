#!/usr/bin/env python3
"""Harbor post-backup safety validation. A helper for native systemd completion actions."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import subprocess

EXPECTED=("/", "/var/lib/machines", "/var/lib/portables", "/var/cache",
          "/home", "/var/log", "/root", "/srv", "/var/tmp")

def validate_machine_set(repo: Path, set_id: str, *, verify_boot: bool = False) -> tuple[bool,str]:
    if not re.fullmatch(r"[a-f0-9-]{36}",set_id) or not repo.is_dir():
        return False,"missing destination"
    catalog=repo/(".harbor-machine-set-"+set_id+".json")
    if not catalog.is_file():
        return False,"machine catalog unavailable"
    try:
        data=json.loads(catalog.read_text())
        if data.get("set_id")!=set_id or data.get("status")!="completed_btrfs_and_boot_files":
            return False,"not fully completed"
        members=data.get("members",[])
        if len(members)!=9 or tuple(x.get("original_mount") for x in members)!=EXPECTED:
            return False,"Btrfs coverage incomplete"
        for member in members:
            if member.get("status")!="completed" or not member.get("transfer_id"):
                return False,"incomplete member"
            name=member["archive"]
            if not re.fullmatch("machine[0-9TZ-]+"+re.escape(set_id[:8])+"-[0-9]{3}",name):
                return False,"invalid archive name"
            archive=repo/(name+".btrfs.zst")
            meta=repo/(name+".btrfs.zst.meta")
            if (not archive.is_file() or archive.is_symlink()
                    or not meta.is_file() or meta.is_symlink()):
                return False,"archive or verification metadata missing"
            doc=json.loads(meta.read_text())
            sha=doc.get("checksum",{})
            if doc.get("size")!=archive.stat().st_size or archive.stat().st_size==0 or (
                sha.get("algorithm")!="sha256" or not re.fullmatch("[a-f0-9]{64}",str(sha.get("value","")))):
                return False,"archive metadata mismatch"
        if list(repo.glob("machine*"+set_id[:8]+"*.part")):
            return False,"incomplete archive still present"
        boot=data.get("boot_members",[])
        if len(boot)!=1 or boot[0].get("status")!="completed" or boot[0].get("mount_point")!="/boot":
            return False,"boot archive incomplete"
        item=boot[0]
        source=repo/item["archive"]
        if not source.is_file() or source.is_symlink() or source.stat().st_size!=item["bytes"]:
            return False,"boot file missing or incomplete"
        if verify_boot:
            h=hashlib.sha256()
            with source.open("rb") as f:
                for piece in iter(lambda:f.read(4*1024*1024),b""):
                    h.update(piece)
            if h.hexdigest()!=item["sha256"]:
                return False,"boot checksum mismatch"
        return True,"nine complete Btrfs members and EFI"
    except (OSError,ValueError,KeyError,TypeError):
        return False,"invalid backup catalog"

def job_in_progress(unit: str)->bool:
    if not re.fullmatch(r"harbor-machine-backup-[a-f0-9-]{36}\.service",unit):
        return True
    cp=subprocess.run(["systemctl","show",unit,"-p","ActiveState","--value"],
                      capture_output=True,text=True,timeout=7)
    return cp.stdout.strip() not in ("inactive","failed","")

def main() -> int:
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=["check-machine"])
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--set-id",required=True)
    parser.add_argument("--unit",required=True)
    args=parser.parse_args()
    if job_in_progress(args.unit):
        print("WAIT: active Harbor backup job")
        return 1
    good,reason=validate_machine_set(args.repo,args.set_id,verify_boot=True)
    print(("READY" if good else "WAIT")+": "+reason)
    return 0 if good else 1

if __name__=="__main__":
    raise SystemExit(main())
