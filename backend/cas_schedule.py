#!/usr/bin/env python3
"""Scheduled FastCDC CAS transport. Snapper remains authoritative.

This module only reads Snapper metadata and runs Harbor Transport on existing
readonly snapshots. Never creates Snapper snapshots or mounts a filesystem.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import subprocess

ARCHIVE_RE = re.compile(r"^snap-([A-Za-z0-9_][A-Za-z0-9_.-]{0,127})-([1-9][0-9]*)$")

def snapper_rows(payload: object, config: str) -> list[dict]:
    if not isinstance(payload, dict) or not isinstance(payload.get(config), list):
        raise ValueError("Snapper JSON does not contain the selected configuration")
    rows = payload[config]
    return [item for item in rows if isinstance(item, dict)]

def eligible_snapshots(rows: list[dict]) -> list[tuple[int, Path]]:
    result = []
    for item in rows:
        number = item.get("number")
        subvolume = item.get("subvolume")
        # Snapper omits 'read-only' on some versions; btrfs property is
        # authoritative and checked again just before btrfs send.
        if type(number) is not int or number < 1:
            continue
        if not isinstance(subvolume,str) or not subvolume.startswith("/"):
            continue
        root = Path(subvolume)
        if ".." in root.parts or str(root) != subvolume.rstrip("/") and subvolume != "/":
            continue
        if item.get("read-only") is False:
            continue
        result.append((number, root / ".snapshots" / str(number) / "snapshot"))
    return sorted(result, reverse=True)

def is_readonly_snapshot(path: Path) -> bool:
    if not path.is_dir() or path.is_symlink():
        return False
    check = subprocess.run(["btrfs", "property", "get", "-ts", str(path), "ro"],
                           capture_output=True, text=True, timeout=12, check=False)
    return check.returncode == 0 and check.stdout.strip() == "ro=true"

def build_send(profile, snapper_bin="snapper", cas_bin="harbor-transport") -> list[str] | None:
    snapshots = subprocess.run([snapper_bin, "--jsonout", "-c", profile.config,
                                "list", "--disable-used-space"],
                               capture_output=True, text=True, timeout=35, check=True)
    rows = eligible_snapshots(snapper_rows(json.loads(snapshots.stdout), profile.config))
    available = [(num, path) for num, path in rows if is_readonly_snapshot(path)]
    if not available:
        raise RuntimeError("Snapper has no accessible readonly snapshot for this configuration")
    latest_num, latest_path = available[0]
    name = f"snap-{profile.config}-{latest_num}"
    inventory = subprocess.run([cas_bin, "list", "--repo", profile.target],
                               capture_output=True, text=True, timeout=45, check=True)
    archives = json.loads(inventory.stdout)
    if not isinstance(archives, list):
        raise RuntimeError("CAS inventory is not a JSON list")
    saved = {item["name"] for item in archives
             if isinstance(item, dict) and isinstance(item.get("name"), str)
             and ARCHIVE_RE.fullmatch(item["name"])}
    if name in saved:
        # A manifest alone does not establish validity; never silently skip
        # a corrupted backup and call the schedule successful.
        subprocess.run([cas_bin, "verify-stream", "--repo", profile.target,
                        "--name", name], check=True)
        return None
    argv = [cas_bin, "send", "--repo", profile.target, "--name", name,
            "--snapshot", str(latest_path), "--experimental", "--retries", "8"]
    parent = next(((num, path) for num, path in available[1:]
                   if f"snap-{profile.config}-{num}" in saved), None)
    if parent is not None:
        number, path = parent
        parent_archive = f"snap-{profile.config}-{number}"
        # An inventory entry alone is not enough. Reject damaged ancestors
        # rather than creating an incremental archive with an unusable base.
        subprocess.run([cas_bin, "verify-stream", "--repo", profile.target,
                        "--name", parent_archive], check=True)
        argv.extend(["--parent", str(path),
                     "--parent-archive", parent_archive])
    if profile.allow_local:
        argv.append("--allow-local")
    return argv

def run_cas_profile(profile) -> int:
    if profile.owner_uid is None or profile.owner_uid <= 0:
        raise ValueError("CAS schedule requires a stored real user UID")
    args = build_send(profile)
    if args is None:
        return 0
    env = os.environ.copy()
    env["PKEXEC_UID"] = str(profile.owner_uid)
    # A multi-hundred-GiB full backup or checksum verification can exceed
    # two hours. The systemd oneshot unit owns job cancellation, and Harbor
    # enforces network retries and repository locks independently.
    # An arbitrary Python subprocess deadline would cause perpetual partial
    # backups on slow NFS or an encrypted remote link.
    return subprocess.run(args, env=env, check=False).returncode
