#!/usr/bin/env python3
"""Durable Harbor CAS jobs, supervised by a persistent systemd template.

No job runs during package installation. start is exclusively user-initiated.
Transfer checkpoints are CAS objects: retry re-reads the Btrfs stream from the
beginning but does not resend verified already-present chunks to the repository.
This does NOT claim byte-offset continuation of the Btrfs source stream.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
from types import SimpleNamespace
import re
import stat
import subprocess
import sys
import time
import uuid

try:
    from .cas_schedule import build_send, is_readonly_snapshot, snapshot_uuid
except ImportError:
    # When installed as an executable under /usr/bin without a package parent.
    from cas_schedule import build_send, is_readonly_snapshot, snapshot_uuid

ROOT = Path("/var/lib/btrfs-assistant-harbor/manual-jobs")
UNIT = "btrfs-assistant-harbor-job@{}.service"
ID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,159}$")
PROGRESS = re.compile(r"^HARBOR_PROGRESS_BYTES=(\d+)$")
RUNNING = {"queued", "running", "retrying"}


def check_id(job_id: str) -> str:
    if not isinstance(job_id, str) or not ID_RE.fullmatch(job_id):
        raise ValueError("Invalid job identifier")
    return job_id


def check_store(root: Path = ROOT) -> None:
    if root.is_symlink():
        raise ValueError("Symlinked job directory forbidden")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    st = root.stat()
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != 0 or (st.st_mode & 0o077):
        raise PermissionError("Job directory must belong to root, mode 0700")


def save(path: Path, payload: dict) -> None:
    if path.is_symlink():
        raise ValueError("Symlinked registry entry forbidden")
    tmp = path.parent / (".tmp-" + uuid.uuid4().hex)
    try:
        with tmp.open("x", encoding="utf-8") as stream:
            os.chmod(tmp, 0o600)
            json.dump(payload, stream, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        tmp.unlink(missing_ok=True)


def load(job_id: str, root: Path = ROOT) -> dict:
    path = root / (check_id(job_id) + ".json")
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 12000:
        raise ValueError("Untrusted or absent job record")
    doc = json.loads(path.read_text(encoding="utf-8"))
    if (doc.get("version") != 1 or doc.get("id") != job_id or
        doc.get("state") not in RUNNING | {"completed", "cancelled", "failed"}):
        raise ValueError("Damaged job state")
    if not isinstance(doc.get("command"), list) or doc["command"][:2] != ["harbor-transport", "send"]:
        raise ValueError("Untrusted transport command")
    if not isinstance(doc.get("owner_uid"), int) or not 1 <= doc["owner_uid"] <= 65534:
        raise ValueError("Invalid initiating desktop user")
    if not isinstance(doc.get("repository"), str) or not doc["repository"].startswith("/"):
        raise ValueError("Invalid repository")
    return doc


def all_jobs(root: Path = ROOT) -> list[dict]:
    if not root.is_dir():
        return []
    result = []
    for path in sorted(root.glob("*.json")):
        if path.is_symlink():
            raise ValueError("Symlinked registry entry forbidden")
        result.append(load(path.stem, root))
    return result


def require_network_repo(repo: str) -> None:
    if not repo.startswith("/") or os.path.normpath(repo) != repo or repo == "/":
        raise ValueError("Unsafe backup destination")
    probe = subprocess.run(
        ["findmnt", "-T", repo, "-n", "-o", "FSTYPE"],
        check=True, capture_output=True, text=True, timeout=15)
    if probe.stdout.strip() not in ("nfs4", "nfs", "cifs", "smb3"):
        raise RuntimeError("Network mount missing: refusing local directory fallback")
    marker = Path(repo) / ".harbor-repo-id"
    if marker.is_symlink() or not marker.is_file():
        raise RuntimeError("CAS repository marker absent or unsafe")


def value_after(argv: list[str], flag: str) -> str:
    if flag not in argv:
        raise ValueError("Job command missing required argument " + flag)
    offset = argv.index(flag) + 1
    if offset >= len(argv):
        raise ValueError("Missing argument value " + flag)
    return argv[offset]


def recorded_archive(doc: dict) -> str:
    args = doc["command"]
    machine = value_after(args, "--machine")
    name = value_after(args, "--name")
    if not SAFE_NAME.fullmatch(machine) or not SAFE_NAME.fullmatch(name):
        raise ValueError("Unsafe archive name or machine identity")
    return f"m@{machine}@{name}"


def check_snapshot_identities(doc: dict) -> None:
    command = doc["command"]
    snapshot = Path(value_after(command, "--snapshot"))
    if not is_readonly_snapshot(snapshot) or snapshot_uuid(snapshot) != doc["source_uuid"]:
        raise ValueError("Original readonly source snapshot changed or was removed")
    if "--parent" in command:
        parent = Path(value_after(command, "--parent"))
        if not is_readonly_snapshot(parent) or snapshot_uuid(parent) != doc["parent_uuid"]:
            raise ValueError("Original readonly incremental parent changed or was removed")


def verify_committed(doc: dict) -> bool:
    archive = recorded_archive(doc)
    # systemd does not inherit PKEXEC_UID. It must be reinstated explicitly
    # for NFS root-squash: the Rust CAS client switches FSUID to the real owner.
    env = {**os.environ, "PKEXEC_UID": str(doc["owner_uid"])}
    cmd = ["/usr/bin/harbor-transport", "list", "--repo", doc["repository"]]
    raw = subprocess.run(cmd, check=True, text=True, capture_output=True,
                         timeout=90, env=env)
    entries = json.loads(raw.stdout)
    if not isinstance(entries, list):
        raise RuntimeError("Invalid repository inventory")
    if not any(isinstance(item, dict) and item.get("name") == archive for item in entries):
        return False
    subprocess.run(
        ["/usr/bin/harbor-transport", "verify-stream", "--repo", doc["repository"],
         "--name", archive], check=True, timeout=7200, env=env)
    return True


def register(config: str, repo: str, machine: str, number: int,
             owner_uid: int, *, root: Path = ROOT, activate: bool = True,
             command_builder=build_send) -> dict:
    if not 1 <= owner_uid <= 65534:
        raise ValueError("A real desktop user UID is required")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", machine):
        raise ValueError("Invalid machine identity")
    if not 1 <= number <= 2**31 - 1:
        raise ValueError("Invalid selected Snapper number")
    require_network_repo(repo)
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,69}", config):
        raise ValueError("Invalid or oversized Snapper configuration")
    # The installed scheduler is named btrfs-assistant-harbor-schedule, NOT
    # remote_schedule.py. Only the read-only attributes required by the
    # existing, fully validated CAS planning logic are needed here.
    profile = SimpleNamespace(config=config, target=repo, allow_local=False,
                              machine=machine, owner_uid=owner_uid)
    # Immutable snap UUID matching, archived-parent verification, and first
    # empty-repository FULL handling live in the existing scheduler helper.
    try:
        argv = command_builder(profile, selected_number=number)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        detail = str(stderr or exc).strip()[:800]
        raise RuntimeError(f"CAS planning failed: {detail}") from exc
    if argv is None:
        return {"state": "already-backed-up"}
    if argv[:2] != ["harbor-transport", "send"] or "--machine" not in argv:
        raise ValueError("Unsafe prepared CAS plan")
    source = Path(value_after(argv, "--snapshot"))
    parent_uuid = snapshot_uuid(Path(value_after(argv, "--parent"))) if "--parent" in argv else None
    doc = dict(version=1, id=str(uuid.uuid4()), state="queued", created=time.time(),
               owner_uid=owner_uid, repository=repo, machine=machine,
               source_uuid=snapshot_uuid(source), parent_uuid=parent_uuid,
               bytes_read=0, attempts=0, command=argv)
    recorded_archive(doc)
    check_store(root)
    lock_file = root / ".lock"
    if lock_file.is_symlink():
        raise ValueError("Unsafe registry lock")
    with lock_file.open("a+b") as lock:
        os.chmod(lock_file, 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        if any(j["state"] in RUNNING and j.get("repository") == repo and
               j.get("machine") == machine for j in all_jobs(root)):
            raise RuntimeError("A manual backup for this machine is already active")
        save(root / (doc["id"] + ".json"), doc)
        if activate:
            try:
                subprocess.run(["systemctl", "enable", "--now", UNIT.format(doc["id"])],
                               check=True, timeout=30)
            except BaseException:
                doc["state"] = "failed"
                save(root / (doc["id"] + ".json"), doc)
                raise
    return {"id": doc["id"], "state": doc["state"], "archive": recorded_archive(doc)}


def disable_completed(job_id: str) -> None:
    subprocess.run(["systemctl", "disable", UNIT.format(job_id)], check=True, timeout=20)


def runner(job_id: str, *, root: Path = ROOT) -> int:
    doc = load(job_id, root)
    if doc["state"] == "completed":
        return 0
    if doc["state"] == "cancelled":
        return 1
    path = root / (job_id + ".json")
    try:
        require_network_repo(doc["repository"])
        # An interrupted attempt may have committed its CAS manifest just
        # before the service died; verify instead of overwriting that archive.
        if verify_committed(doc):
            doc["state"] = "completed"
            doc["exit_code"] = 0
            save(path, doc)
            disable_completed(job_id)
            return 0
        check_snapshot_identities(doc)
        doc["state"] = "running"
        doc["attempts"] += 1
        doc["last_started"] = time.time()
        save(path, doc)
        command = list(doc["command"])
        command[0] = "/usr/bin/harbor-transport"
        env = {**os.environ, "PKEXEC_UID": str(doc["owner_uid"])}
        last_written = time.monotonic()
        with subprocess.Popen(command, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, bufsize=1) as proc:
            assert proc.stdout is not None
            for line in proc.stdout:
                print(line, end="", flush=True)
                match = PROGRESS.fullmatch(line.strip())
                if match:
                    doc["bytes_read"] = int(match.group(1))
                if time.monotonic() - last_written > 2.5:
                    if load(job_id, root)["state"] == "cancelled":
                        proc.terminate()
                        break
                    save(path, doc)
                    last_written = time.monotonic()
            code = proc.wait()
        if load(job_id, root)["state"] == "cancelled":
            return 1
        if code != 0:
            raise RuntimeError(f"CAS send returned {code}; will retry")
        if not verify_committed(doc):
            raise RuntimeError("CAS command exited successfully without a verified archive")
        doc["state"] = "completed"
        doc["last_finished"] = time.time()
        doc["exit_code"] = 0
        save(path, doc)
        disable_completed(job_id)
        return 0
    except Exception as exc:
        if load(job_id, root)["state"] != "cancelled":
            doc["state"] = "retrying"
            doc["last_error"] = str(exc)[:500]
            save(path, doc)
        print(f"Harbor service retry: {exc}", file=sys.stderr, flush=True)
        return 1


def cancel(job_id: str, *, root: Path = ROOT, perform_systemd: bool = True) -> dict:
    doc = load(job_id, root)
    if doc["state"] == "completed":
        raise ValueError("Completed archives are immutable")
    doc["state"] = "cancelled"
    doc["cancelled_at"] = time.time()
    save(root / (job_id + ".json"), doc)
    if perform_systemd:
        subprocess.run(["systemctl", "disable", "--now", UNIT.format(job_id)],
                       check=True, timeout=30)
    return {"id": job_id, "state": doc["state"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    start = sub.add_parser("start")
    start.add_argument("--repo", required=True)
    start.add_argument("--machine", required=True)
    start.add_argument("--snapper-config", required=True)
    start.add_argument("--snapper-number", type=int, required=True)
    for name in ("run", "cancel", "status"):
        sub.add_parser(name).add_argument("--id", required=True)
    sub.add_parser("list")
    sub.add_parser("cancel-all")
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error("Only the authenticated privileged Harbor backend may manage jobs")
    if args.action == "start":
        uid = os.environ.get("PKEXEC_UID", "")
        if not uid.isdecimal():
            parser.error("Missing original non-root UID from polkit")
        output = register(args.snapper_config, args.repo, args.machine,
                          args.snapper_number, int(uid))
        print(json.dumps(output))
    elif args.action == "run":
        return runner(check_id(args.id))
    elif args.action in ("cancel", "status", "list", "cancel-all"):
        desktop_uid = os.environ.get("PKEXEC_UID", "")
        if not desktop_uid.isdecimal() or not 1 <= int(desktop_uid) <= 65534:
            parser.error("Authenticated original desktop UID required")
        uid = int(desktop_uid)
        if args.action in ("cancel", "status"):
            doc = load(check_id(args.id))
            if doc["owner_uid"] != uid:
                parser.error("Job belongs to another desktop user")
            print(json.dumps(cancel(args.id) if args.action == "cancel" else doc))
        elif args.action == "list":
            print(json.dumps([x for x in all_jobs() if x["owner_uid"] == uid]))
        else:
            changed = [cancel(x["id"]) for x in all_jobs()
                       if x["owner_uid"] == uid and x["state"] in RUNNING]
            print(json.dumps(changed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
