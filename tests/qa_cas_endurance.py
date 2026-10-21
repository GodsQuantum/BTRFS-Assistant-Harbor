#!/usr/bin/env python3
"""Bounded Linux CAS endurance on a disposable repo (no real backups)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import resource
import subprocess
import tempfile
import time

def cmd(binary, *args):
    run = subprocess.run([str(binary), *map(str,args)],capture_output=True,text=True,timeout=120)
    if run.returncode:
        raise RuntimeError(f'CAS command failed rc={run.returncode} args={args} stderr={run.stderr[-4000:]}')
    return json.loads(run.stdout)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--binary',type=Path,required=True)
    parser.add_argument('--temp-root',type=Path,required=True)
    parser.add_argument('--rounds',type=int,default=40)
    parser.add_argument('--payload-mib',type=int,default=12)
    args=parser.parse_args()
    assert 5<=args.rounds<=100
    started=time.monotonic()
    rng=random.Random(20261021)
    with tempfile.TemporaryDirectory(dir=args.temp_root,prefix='R46-local-cas-endurance-') as tmp:
        root=Path(tmp)
        repo=root/'Workstations'
        repo.mkdir()
        cmd(args.binary,'init','--repo',repo,'--allow-local')
        seed=rng.randbytes(12*1024*1024)
        src=root/'payload.bin'
        restored=root/'restore.bin'
        report=[]
        archives=[]
        for i in range(args.rounds):
            # First common payload; newer revisions inject bounded changes.
            payload=(b'prefix-'+str(i//2).encode()+b'|' if i%4 else b'')+seed
            src.write_bytes(payload)
            machine='Pegasus' if i%2==0 else 'Galactica'
            archive=f'snap-root-{i:03d}-20261021T150000Z'
            name=f'm@{machine}@{archive}'
            before=time.monotonic()
            stats=cmd(args.binary,'ingest-file','--repo',repo,'--machine',machine,'--name',archive,'--file',src,'--experimental','--allow-local')
            cmd(args.binary,'verify','--repo',repo,'--name',name)
            if i%4==3:
                cmd(args.binary,'recover-file','--repo',repo,'--name',name,'--output',restored)
                assert restored.read_bytes()==payload
                restored.unlink()
            report.append({'round':i,'machine':machine,'elapsed_s':round(time.monotonic()-before,3),'new':stats['new_objects'],'reused':stats['reused_objects']})
            archives.append(name)
        # Deleting every Pegasus archive must preserve each Galactica archive.
        to_delete=[n for n in archives if n.startswith('m@Pegasus@')]
        plan=cmd(args.binary,'prune','--repo',repo,*sum((['--name',n] for n in to_delete),[]))['plan']
        cmd(args.binary,'prune','--repo',repo,*sum((['--name',n] for n in to_delete),[]),'--confirm-plan',plan['plan_sha256'])
        assert len(cmd(args.binary,'list','--repo',repo))==len(archives)//2
        for name in archives:
            if name.startswith('m@Galactica@'):
                cmd(args.binary,'verify','--repo',repo,'--name',name)
        rss_kb=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        out={'status':'PASS','rounds':args.rounds,'seconds':round(time.monotonic()-started,2),'max_child_rss_kib':rss_kb,
            'total_new_chunks':sum(r['new'] for r in report),'total_reused_chunks':sum(r['reused'] for r in report),
            'gc_reclaimed_objects':plan['orphan_objects'],'retained_archives':len(archives)//2,
            'peak_single_round_s':max(r['elapsed_s'] for r in report),'results':report}
        print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
