#!/usr/bin/env python3
"""Read-only Harbor job observer publishing minimal, non-secret status to /run.

This separate process never signals/restarts Btrfs send jobs. It can attach to
a job started before this monitor was installed. Snapshot-size forecasts are
rough bounds, NOT a second btrfs send or a promise of exact stream sizes.
"""
from __future__ import annotations
import concurrent.futures
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time

try:
    from backend.manual_jobs import ROOT, all_jobs, RUNNING, value_after
except ImportError:
    # Installed /usr/bin CLI has no .py suffix; never spawn a subprocess
    # or parse sensitive job state in the unprivileged Qt process.
    import runpy
    legacy = runpy.run_path("/usr/bin/btrfs-assistant-harbor-job",
                            run_name="harbor_progress_import")
    ROOT = legacy["ROOT"]
    all_jobs = legacy["all_jobs"]
    RUNNING = legacy["RUNNING"]
    value_after = legacy["value_after"]

PUBLIC = Path("/run/btrfs-assistant-harbor")
UNIT = "btrfs-assistant-harbor-job@{}.service"
BYTE_ROW = re.compile(r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+\S+")
MAX_JOBS = 30
GIB = 1024 ** 3
MACHINE_UNIT = re.compile(
    r"^harbor-machine-backup-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
    r"[0-9a-f]{4}-[0-9a-f]{12}\.service$"
)
MACHINE_FIELDS = (
    "completed_members", "total_members", "bytes_written",
    "estimated_total_bytes", "estimated_percent", "eta_seconds",
    "bytes_per_second", "eta_stalled",
)


def machine_live_status() -> dict[int, dict]:
    """Read sanitized in-flight checkpoint-v2 machine metrics via journald.

    The actual backup stays in its existing systemd unit. No extra stream,
    filesystem traversal or mutable per-job lock is needed for the UI.
    """
    try:
        result = subprocess.run(
            ["systemctl", "list-units", "--no-legend", "--no-pager",
             "--plain", "--type=service", "--state=running",
             "harbor-machine-backup-*.service"],
            capture_output=True, text=True, timeout=5, check=False)
    except (OSError, subprocess.SubprocessError):
        return {}
    if result.returncode:
        return {}
    users: dict[int, dict] = {}
    for line in result.stdout.splitlines()[:8]:
        unit = line.strip().split(maxsplit=1)[0] if line.strip() else ""
        if not MACHINE_UNIT.fullmatch(unit):
            continue
        try:
            env = subprocess.run(
                ["systemctl", "show", unit, "--property=Environment", "--value"],
                capture_output=True, text=True, timeout=4, check=False)
            owner = re.search(r"(?:^|\s)HARBOR_OWNER_UID=(\d{1,10})(?:\s|$)",
                              env.stdout)
            if env.returncode or not owner:
                continue
            uid = int(owner.group(1))
            if uid < 1 or uid > 4294967294:
                continue
            logs = subprocess.run(
                ["journalctl", "--unit", unit, "--output=cat",
                 "--no-pager", "-n", "80"],
                capture_output=True, text=True, timeout=5, check=False)
            if logs.returncode:
                continue
        except (OSError, subprocess.SubprocessError):
            continue
        sample = None
        for raw in logs.stdout.splitlines()[-80:]:
            if len(raw) > 8192 or not raw.startswith("{"):
                continue
            try:
                candidate = json.loads(raw)
            except (ValueError, TypeError):
                continue
            if isinstance(candidate, dict) and candidate.get("event") == "machine_progress":
                sample = candidate
        status = {"state": "running"}
        if sample:
            for key in MACHINE_FIELDS:
                val = sample.get(key)
                if key == "eta_stalled" and isinstance(val, bool):
                    status[key] = val
                elif type(val) in (int, float) and 0 <= val < 2**62:
                    status[key] = val
        users[uid] = status
    return users


def measure_snapshot(snapshot: str, timeout: int = 110) -> int | None:
    if not snapshot.startswith("/") or "\x00" in snapshot:
        return None
    try:
        check = subprocess.run(["btrfs", "filesystem", "du", "--raw", "-s", snapshot],
                               capture_output=True, text=True, timeout=timeout, check=True)
        for line in check.stdout.splitlines():
            m = BYTE_ROW.match(line)
            if m:
                return int(m.group(1))
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return None


def safe_unit_state(jobid: str) -> bool:
    try:
        return subprocess.run(["systemctl", "is-active", "--quiet", UNIT.format(jobid)],
                              timeout=4, check=False).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False




def nfs_write_counter(repo: str, mountstats: Path = Path("/proc/self/mountstats")) -> int | None:
    """Read kernel NFS mount WRITE payload bytes, not Btrfs-stream bytes.

    Shared mount write traffic from other apps may be included. Measurements
    start when the monitor attaches, not retrospectively.
    """
    try:
        contents = mountstats.read_text()
    except OSError:
        return None
    selected = (-1, None)
    path = ""
    nfs = False
    for line in contents.splitlines():
        if line.startswith("device ") and " mounted on " in line and " with fstype " in line:
            path = line.split(" mounted on ", 1)[1].split(" with fstype ", 1)[0]
            nfs = " with fstype nfs" in line
        elif nfs and line.lstrip().startswith("bytes:"):
            tokens = line.partition("bytes:")[2].split()
            if len(tokens) >= 6 and (repo == path or repo.startswith(path.rstrip("/") + "/")):
                try:
                    candidate = int(tokens[5])  # serverwritebytes (NFS RPC payload)
                except ValueError:
                    continue
                if len(path) > selected[0]:
                    selected = (len(path), candidate)
    return selected[1]

def synthesize(job: dict, now: float, last: dict | None, source_size: int | None,
               active: bool, network_observed: int | None = None,
               network_rate_ratio: float | None = None) -> dict:
    read = max(0, int(job.get("bytes_read", 0)))
    uploaded = max(0, int(job.get("uploaded_bytes", 0)))
    reused = max(0, int(job.get("reused_bytes", 0)))
    upload_available = bool(job.get("upload_metrics_available", False))
    started = float(job.get("last_started", job.get("created", now)))
    attempt = int(job.get("attempts", 0))
    prior = last if last and last.get("attempt") == attempt else None
    speed = 0.0
    if prior and now > prior["timestamp"]:
        delta = read - prior["bytes_read"]
        dt = now - prior["timestamp"]
        if delta >= 0 and dt >= 1:
            instantaneous = delta / dt
            speed = 0.55 * instantaneous + 0.45 * max(0, float(prior.get("speed_bytes_s", 0)))
    elif started < now - 25 and read > 0:
        # Historical average on attach to an existing job; labelled approximate.
        speed = read / max(1.0, now - started)
    # The raw btrfs stream includes send protocol metadata; its total is
    # not computable from snapshot FIEMAP alone. Add a conservative margin.
    total = None
    if source_size and "--parent" not in job.get("command", []):
        total = max(int(source_size * 1.12), int(read * 1.03))
    remains = max(0, total - read) if total else None
    eta = int(remains / speed) if remains is not None and speed >= 128 * 1024 else None
    # For future jobs Rust emits exact compressed new-object bytes and reused
    # stream bytes. Extrapolation is a forecast, never report it as transferred.
    estimated_network_remains = (int(remains * uploaded / max(1, read))
                                 if upload_available and remains is not None and read >= 16 * 1024 * 1024
                                 else (int(remains * network_rate_ratio) if remains is not None
                                       and network_rate_ratio is not None else None))
    state = job.get("state", "unknown")
    if state == "running" and not active:
        state = "stale"
    return dict(version=1, id=job["id"], machine=job.get("machine", ""),
                state=state, attempt=attempt, timestamp=now, started=started,
                bytes_read=read, uploaded_bytes=uploaded if upload_available else None,
                reused_bytes=reused if upload_available else None,
                nfs_observed_bytes=network_observed,
                nfs_observation_is_shared=True,
                upload_metrics_available=upload_available,
                snapshot_bytes_estimate=source_size,
                stream_total_estimate=total,
                stream_remaining_estimate=remains,
                network_remaining_estimate=estimated_network_remains,
                speed_bytes_s=int(speed), eta_seconds=eta,
                progress_percent_estimate=round(100 * read / total, 1) if total else None,
                estimate_is_approximate=True)


def publish(uid: int, jobs: list[dict], dest: Path = PUBLIC,
            machine: dict | None = None) -> None:
    # /run/btrfs-assistant-harbor is always root-owned, no user-writable dirs.
    if dest.is_symlink():
        raise RuntimeError("Unsafe status directory")
    dest.mkdir(mode=0o755, parents=True, exist_ok=True)
    if dest.stat().st_uid != os.geteuid() or dest.stat().st_mode & 0o022:
        raise RuntimeError("Status directory must be root-owned and not writable by users")
    destfile = dest / f"{uid}.json"
    tmp = dest / f".{uid}.{os.getpid()}.tmp"
    try:
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
        with os.fdopen(fd, "w") as f:
            payload = dict(version=1, updated=time.time(), jobs=jobs)
            if machine:
                payload["machine_backup"] = machine
            json.dump(payload, f)
            f.write("\n")
        os.replace(tmp, destfile)
    finally:
        tmp.unlink(missing_ok=True)


def observe(once=False, *, registry=ROOT, dest=PUBLIC, interval=5,
            measure=measure_snapshot, service=safe_unit_state):
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    size_futures: dict[str, concurrent.futures.Future] = {}
    history: dict[str, dict] = {}
    network_samples: dict[str, tuple[int, int, float]] = {}
    try:
        while True:
            now = time.time()
            jobs = all_jobs(registry)[-MAX_JOBS:]
            visible: dict[int, list[dict]] = {}
            for doc in jobs:
                job_id = doc["id"]
                if doc["state"] in RUNNING and job_id not in size_futures:
                    try:
                        snapshot = value_after(doc["command"], "--snapshot")
                        size_futures[job_id] = pool.submit(measure, snapshot)
                    except ValueError:
                        pass
                future = size_futures.get(job_id)
                size = future.result() if future and future.done() else None
                if future and future.done():
                    # Cache completed size without holding a Future forever.
                    size_futures[job_id] = future
                observed = None
                nfs_ratio = None
                if doc["state"] in RUNNING:
                    counter = nfs_write_counter(doc.get("repository", ""))
                    sample = network_samples.get(job_id)
                    if counter is not None and sample is None:
                        network_samples[job_id] = (counter, int(doc.get("bytes_read", 0)), now)
                    elif counter is not None and sample is not None:
                        first_counter, first_read, first_time = sample
                        observed = max(0, counter - first_counter)
                        delta_read = int(doc.get("bytes_read", 0)) - first_read
                        if delta_read >= 16 * 1024 * 1024 and now - first_time >= 10:
                            nfs_ratio = min(4.0, observed / delta_read)
                current = synthesize(doc, now, history.get(job_id), size,
                                     service(job_id) if doc["state"] in RUNNING else False,
                                     network_observed=observed, network_rate_ratio=nfs_ratio)
                history[job_id] = current
                visible.setdefault(doc["owner_uid"], []).append(current)
            machines = machine_live_status()
            for uid in machines:
                visible.setdefault(uid, [])
            for uid, records in visible.items():
                publish(uid, records, dest, machine=machines.get(uid))
            if once:
                break
            time.sleep(interval)
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


if __name__ == "__main__":
    if os.geteuid() != 0:
        sys.exit("Harbor progress observer requires root for protected job metadata")
    observe(once="--once" in sys.argv)
