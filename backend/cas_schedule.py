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
import uuid

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

def snapshot_uuid(path: Path) -> str:
    """Read the immutable Btrfs snapshot UUID, not a recycled Snapper number."""
    result = subprocess.run(
        ["btrfs", "subvolume", "show", str(path)],
        capture_output=True, text=True, timeout=30, check=True)
    for line in result.stdout.splitlines():
        key, separator, value = line.strip().partition(":")
        if separator and key == "UUID":
            parsed = uuid.UUID(value.strip())
            if parsed.int == 0:
                break
            return str(parsed)
    raise RuntimeError("Snapshot UUID cannot be established safely")

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
    if getattr(profile, "machine", None) is not None:
        return build_machine_send(profile, available, archives, cas_bin)
    saved = {item["name"] for item in archives
             if isinstance(item, dict) and isinstance(item.get("name"), str)
             and ARCHIVE_RE.fullmatch(item["name"])}
    if name in saved:
        # Snapper can reuse a snapshot number after pruning. An existing
        # immutable archive with that numeric name may represent a DIFFERENT
        # source. Checking only its content hashes would falsely mark the
        # newly created snapshot as backed up. Never silently skip it.
        matches = [item for item in archives if isinstance(item, dict)
                   and item.get("name") == name]
        if len(matches) != 1:
            raise RuntimeError("Duplicate CAS archive name in inventory")
        saved_uuid = matches[0].get("source_uuid")
        if not isinstance(saved_uuid, str):
            raise RuntimeError("Existing CAS archive lacks Btrfs source UUID; cannot skip")
        try:
            expected_uuid = str(uuid.UUID(saved_uuid))
        except ValueError as exc:
            raise RuntimeError("Invalid archived source UUID") from exc
        if expected_uuid != snapshot_uuid(latest_path):
            raise RuntimeError(
                "Snapper snapshot number reused: CAS archive UUID differs from current source; "
                "refusing to skip an unsaved snapshot. Preserve old archive and select a "
                "collision-safe new archive name before proceeding."
            )
        # A manifest alone does not establish validity; never silently skip
        # a corrupted backup and call the schedule successful.
        subprocess.run([cas_bin, "verify-stream", "--repo", profile.target,
                        "--name", name], check=True)
        return None
    argv = [cas_bin, "send", "--repo", profile.target, "--name", name,
            "--snapshot", str(latest_path), "--experimental", "--retries", "8"]
    # Snapper can also recycle the number of an older candidate parent.
    # Never send a delta against an archived parent with a different Btrfs
    # UUID. Fall back to a complete send; retaining the previous archive
    # is mandatory because it may anchor older incremental chains.
    indexed = {item["name"]: item for item in archives if isinstance(item, dict)
               and isinstance(item.get("name"), str) and item["name"] in saved}
    parent = None
    for number, path in available[1:]:
        candidate = indexed.get(f"snap-{profile.config}-{number}")
        if candidate is None:
            continue
        archived_uuid = candidate.get("source_uuid")
        if not isinstance(archived_uuid, str):
            continue
        try:
            recorded = str(uuid.UUID(archived_uuid))
        except ValueError:
            continue
        if recorded == snapshot_uuid(path):
            parent = (number, path)
            break
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


def build_machine_send(profile, available: list[tuple[int, Path]], archives: list[dict],
                       cas_bin: str) -> list[str] | None:
    """Use one shared repository, but only this machine's committed parents."""
    from datetime import datetime, timezone
    machine = profile.machine
    prefix = f"m@{machine}@snap-{profile.config}-"
    saved = [item for item in archives if isinstance(item, dict)
             and isinstance(item.get("name"), str)
             and item["name"].startswith(prefix)]
    latest_num, latest_path = available[0]
    latest_uuid = snapshot_uuid(latest_path)
    latest_prefix = prefix + str(latest_num) + "-"
    completed = [item for item in saved if item["name"].startswith(latest_prefix)
                 and item.get("source_uuid") == latest_uuid]
    if completed:
        name = max(item["name"] for item in completed)
        subprocess.run([cas_bin, "verify-stream", "--repo", profile.target,
                        "--name", name], check=True)
        return None
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    basename = f"snap-{profile.config}-{latest_num}-{timestamp}-{uuid.uuid4().hex}"
    argv = [cas_bin, "send", "--repo", profile.target,
            "--name", basename, "--machine", machine,
            "--snapshot", str(latest_path), "--experimental", "--retries", "8"]
    for number, path in available[1:]:
        expected = snapshot_uuid(path)
        candidates = [item for item in saved
                      if item["name"].startswith(prefix + str(number) + "-")
                      and item.get("source_uuid") == expected]
        if not candidates:
            continue
        parent = max(item["name"] for item in candidates)
        subprocess.run([cas_bin, "verify-stream", "--repo", profile.target,
                        "--name", parent], check=True)
        argv.extend(["--parent", str(path), "--parent-archive", parent])
        break
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
