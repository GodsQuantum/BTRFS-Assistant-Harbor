#!/usr/bin/env python3
"""Concurrent *process* writers, shared CAS objects, stale-plan rejection and GC.

Only temporary repositories are used. No real mounts, Snapper configs, devices
or production backups are accessed.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import random
import subprocess
import tempfile
import time

def run(binary: Path, *args: object, ok: bool = True):
    response = subprocess.run([str(binary), *(str(a) for a in args)],
                              capture_output=True, text=True, timeout=180)
    if ok:
        if response.returncode != 0:
            raise RuntimeError(f"Failed rc={response.returncode} {args}: {response.stderr[-3000:]}")
        return json.loads(response.stdout)
    if response.returncode == 0:
        raise AssertionError(f"Unsafe success for expected rejection {args}")
    return response.stderr[-3000:]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--binary",type=Path,required=True)
    ap.add_argument("--temp-root",type=Path,required=True)
    ap.add_argument("--workers",type=int,default=8)
    ap.add_argument("--archives-per-machine",type=int,default=12)
    a=ap.parse_args()
    assert 2<=a.workers<=16 and 2<=a.archives_per_machine<=50
    started=time.monotonic()
    original=random.Random(20261021).randbytes(8*1024*1024)
    with tempfile.TemporaryDirectory(prefix="harbor-cas-two-process-clients-",dir=a.temp_root) as directory:
        base=Path(directory)
        repo=base/"Workstations"
        repo.mkdir()
        init=run(a.binary,"init","--repo",repo,"--allow-local")
        immutable=base/"immutable.bin"
        immutable.write_bytes(original)
        tasks=[(machine,f"qa-{i:03d}-20261021T210000Z") for machine in ("Pegasus","Galactica")
               for i in range(a.archives_per_machine)]
        def upload(pair):
            machine,name=pair
            result=run(a.binary,"ingest-file","--repo",repo,"--machine",machine,
                       "--name",name,"--file",immutable,"--allow-local","--experimental")
            return machine,name,result
        uploads=[]
        with ThreadPoolExecutor(max_workers=a.workers) as executor:
            futures=[executor.submit(upload,pair) for pair in tasks]
            for result in as_completed(futures):
                uploads.append(result.result())
        # Creation is serialized by the *global* repo lock, not by the test's
        # executor; after one commit, no subsequent identical payload needs a
        # separate machine object pool.
        newly_created=sum(int(x[2]["new_objects"]) for x in uploads)
        reused=sum(int(x[2]["reused_objects"]) for x in uploads)
        assert newly_created>0
        assert sum(int(x[2]["new_objects"])>0 for x in uploads)==1,uploads
        assert reused>0
        assert not (repo/"machines/Pegasus/objects").exists()
        assert not (repo/"machines/Galactica/objects").exists()
        listed=run(a.binary,"list","--repo",repo)
        assert len(listed)==len(tasks)
        ordered=[f"m@{m}@{name}" for m,name,_ in uploads]
        assert {x["name"] for x in listed}==set(ordered)
        # A preview becomes stale when a second client commits an archive.
        deletions=sorted(x for x in ordered if x.startswith("m@Pegasus@"))
        selection=sum((["--name",name] for name in deletions),[])
        preview=run(a.binary,"prune","--repo",repo,*selection)["plan"]
        extra_name="m@Galactica@new-after-dryrun"
        run(a.binary,"ingest-file","--repo",repo,"--machine","Galactica",
            "--name","new-after-dryrun","--file",immutable,
            "--experimental","--allow-local")
        reject=run(a.binary,"prune","--repo",repo,*selection,
                   "--confirm-plan",preview["plan_sha256"],ok=False)
        assert "repository changed" in reject or "plan" in reject.lower(),reject
        actual=run(a.binary,"prune","--repo",repo,*selection)["plan"]
        assert actual["plan_sha256"]!=preview["plan_sha256"]
        run(a.binary,"prune","--repo",repo,*selection,
            "--confirm-plan",actual["plan_sha256"])
        remain=run(a.binary,"list","--repo",repo)
        assert len(remain)==a.archives_per_machine+1
        for item in remain:
            assert item["name"].startswith("m@Galactica@")
            run(a.binary,"verify","--repo",repo,"--name",item["name"])
        recover=base/"recovered.bin"
        run(a.binary,"recover-file","--repo",repo,"--name",extra_name,"--output",recover)
        assert hashlib.sha256(recover.read_bytes()).digest()==hashlib.sha256(original).digest()
        print(json.dumps({"status":"PASS","repository_id":init["repo_id"],
                          "concurrent_processes":a.workers,"committed_archives":len(uploads)+1,
                          "retained_archives":len(remain),"new_objects":newly_created,
                          "reused_objects":reused,"stale_gc_confirm_rejected":True,
                          "remaining_data_sha256":hashlib.sha256(recover.read_bytes()).hexdigest(),
                          "seconds":round(time.monotonic()-started,2)},sort_keys=True))
if __name__=="__main__":
    main()
