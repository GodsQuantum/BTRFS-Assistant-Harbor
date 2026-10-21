#!/usr/bin/env python3
"""Isolated real-binary CAS inter-machine E2E fixture, never touches a user repo."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import subprocess
import tempfile

def run(binary, *args, success=True):
    completed = subprocess.run([binary, *map(str, args)], capture_output=True,
                               text=True, timeout=240, check=False)
    if success and completed.returncode:
        raise AssertionError(f"failed {args}: rc={completed.returncode}: {completed.stderr}")
    if not success:
        assert completed.returncode != 0, f"unsafe success: {args}"
        return completed.returncode
    try:
        return json.loads(completed.stdout)
    except ValueError as error:
        raise AssertionError(f"invalid JSON from {args}: {completed.stdout!r}") from error

def test(binary, temp_root):
    with tempfile.TemporaryDirectory(prefix="harbor-two-machines-", dir=temp_root) as directory:
        base = Path(directory)
        root = base / "Workstations"
        root.mkdir()
        ready = run(binary, "init", "--repo", root, "--allow-local")
        assert ready["status"] == "initialized"
        assert (root / ".harbor-repo-id").is_file()
        rng = random.Random(20261021)
        original = rng.randbytes(12 * 1024 * 1024)
        payload = base / "shared.bin"
        payload.write_bytes(original)
        a = run(binary, "ingest-file", "--repo", root, "--machine", "Pegasus",
                "--name", "root-snap42-20261021T020000Z",
                "--file", payload, "--experimental", "--allow-local")
        b = run(binary, "ingest-file", "--repo", root, "--machine", "Galactica",
                "--name", "home-snap17-20261021T020001Z",
                "--file", payload, "--experimental", "--allow-local")
        assert a["new_objects"] > 0
        assert b["new_objects"] == 0 and b["reused_objects"] > 0
        assert not (root / "machines/Pegasus/objects").exists()
        assert not (root / "machines/Galactica/objects").exists()
        a_name = "m@Pegasus@root-snap42-20261021T020000Z"
        b_name = "m@Galactica@home-snap17-20261021T020001Z"
        assert (root / "machines/Pegasus/manifests/root-snap42-20261021T020000Z.json").exists()
        assert (root / "machines/Galactica/manifests/home-snap17-20261021T020001Z.json").exists()
        altered = b"new-prefix-20261021" + original
        payload.write_bytes(altered)
        a2_name = "m@Pegasus@root-snap43-20261021T030000Z"
        a2 = run(binary, "ingest-file", "--repo", root, "--machine", "Pegasus",
                 "--name", "root-snap43-20261021T030000Z",
                 "--file", payload, "--experimental", "--allow-local")
        assert a2["reused_objects"] > 0
        assert sorted(x["name"] for x in run(binary, "list", "--repo", root)) == sorted([a_name, a2_name, b_name])
        restored = base / "Galactica.restore"
        run(binary, "recover-file", "--repo", root, "--name", b_name, "--output", restored)
        assert restored.read_bytes() == original
        legacy = "old__legacy_snapshot"
        payload.write_bytes(b"historic" * 200)
        run(binary, "ingest-file", "--repo", root, "--name", legacy,
            "--file", payload, "--experimental", "--allow-local")
        assert (root / f"manifests/{legacy}.json").exists()
        selected = [a_name, a2_name]
        preview = run(binary, "prune", "--repo", root,
                      "--name", a_name, "--name", a2_name)
        plan = preview["plan"]
        assert set(plan["retain_archives"]) == {b_name, legacy}
        cmd = ["prune", "--repo", root, "--name", a_name, "--name", a2_name]
        run(binary, *cmd, "--confirm-plan", plan["plan_sha256"])
        run(binary, "verify", "--repo", root, "--name", b_name)
        assert restored.read_bytes() == original
        remain = sorted(x["name"] for x in run(binary, "list", "--repo", root))
        assert remain == sorted([b_name, legacy])
        return dict(repository_id=ready["repo_id"],
                    full_new_chunks=a["new_objects"], cross_machine_reused=b["reused_objects"],
                    cross_machine_new=b["new_objects"],
                    amended_reused=a2["reused_objects"],
                    reclaimed_objects=plan["orphan_objects"],
                    remaining_archives=remain,
                    source_sha256=hashlib.sha256(original).hexdigest(),
                    restore_sha256=hashlib.sha256(restored.read_bytes()).hexdigest())

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--binary", required=True)
    p.add_argument("--temp-root", required=True)
    args = p.parse_args()
    print(json.dumps(test(args.binary, args.temp_root), sort_keys=True))
