"""Prepare *inactive* alternative Btrfs roots from verified Harbor receive.

Never rename/delete an existing subvolume, touch /boot, boot entries, LUKS,
a mounted active root or machine configuration. The only operations allowed
are snapshots with NEW names on a privately mounted Btrfs subvolid=5 volume.
There is intentionally no boot activation API in this module.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
from typing import Callable

from .cachyos_activation_plan import ActivationPlan

_LEAF = re.compile(r"^@harbor-[0-9a-f]{8}-(?:root|[A-Za-z0-9_-]{1,120})$")


def _mount_type_options(path: Path) -> tuple[str, str]:
    result = subprocess.run(
        ["findmnt", "-rn", "-o", "FSTYPE,OPTIONS", "--mountpoint", str(path)],
        capture_output=True, text=True, timeout=10, check=False,
    )
    if result.returncode or not result.stdout.strip():
        raise ValueError("inactive target must be an exact mounted Btrfs top level")
    fields = result.stdout.split(maxsplit=1)
    if len(fields) != 2:
        raise ValueError("invalid mount metadata")
    return fields[0], fields[1]


def _filesystem_uuid(path: Path) -> str:
    result = subprocess.run(
        ["findmnt", "-rn", "-o", "UUID", "--target", str(path)],
        capture_output=True, text=True, timeout=10, check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def prepare_inactive_subvolumes(
    plan: ActivationPlan,
    received: dict[str, Path],
    *,
    staging: Path,
    top_level: Path,
    probe_mount: Callable[[Path], tuple[str, str]] = _mount_type_options,
    probe_uuid: Callable[[Path], str] = _filesystem_uuid,
    run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> dict[str, str]:
    """Create namespaced NEW rw snapshot roots. Never overwrite an existing OS.

    A failed mid-plan operation leaves forensically useful partial new
    @harbor-* snapshots. Retrying refuses if any destination exists; cleanup
    must be an explicit separate reviewed action, not an automatic rm.
    """
    if os.geteuid() != 0:
        raise PermissionError("inactive Btrfs preparation requires root")
    if plan.bootable_certified or not plan.requires_offline_activation:
        raise ValueError("unexpected activation certificate")
    if not (top_level.is_absolute() and staging.is_absolute()) or (
            top_level == Path("/") or top_level.is_symlink()
            or staging.is_symlink() or not top_level.is_dir() or not staging.is_dir()):
        raise ValueError("unsafe Btrfs preparation root")
    fs, options = probe_mount(top_level)
    if fs != "btrfs" or not re.search(r"(?:^|,)subvolid=5(?:,|$)", options):
        raise ValueError("requires separately mounted Btrfs top-level subvolid=5")
    source_uuid = probe_uuid(staging)
    target_uuid = probe_uuid(top_level)
    if (not source_uuid or source_uuid != target_uuid):
        raise ValueError("received snapshots do not belong to the target Btrfs filesystem")
    expected = dict(plan.mounts)
    if not expected or set(expected) != set(received) or "/" not in expected:
        raise ValueError("received subvolume coverage differs from machine plan")
    prepared: dict[str, str] = {}
    seen_names = set()
    # COMPLETE preflight before first write.
    for mount, child in expected.items():
        basename = child.lstrip("/")
        if (not _LEAF.fullmatch(basename) or basename in seen_names or
                "/" in basename):
            raise ValueError("unsafe/duplicate restored target name")
        seen_names.add(basename)
        source = received[mount]
        if source.is_symlink() or not source.is_dir():
            raise ValueError("missing received readonly subvolume")
        if not source.resolve().is_relative_to(staging.resolve()):
            raise ValueError("source outside verified recovery staging")
        destination = top_level / basename
        if destination.exists() or destination.is_symlink():
            raise ValueError("inactive restored target already exists")
        probe = run(
            ["btrfs", "property", "get", "-ts", str(source), "ro"],
            check=False, capture_output=True, text=True, timeout=20,
        )
        if probe.returncode != 0 or "ro=true" not in probe.stdout:
            raise ValueError("received source is not a readonly Btrfs snapshot")
        prepared[mount] = str(destination)
    for mount, destination in prepared.items():
        source = received[mount]
        result = run(
            ["btrfs", "subvolume", "snapshot", str(source), destination],
            check=False, capture_output=True, text=True, timeout=120,
        )
        if result.returncode:
            raise RuntimeError("cannot prepare inactive Btrfs volume: " +
                               result.stderr.strip()[:180])
    return prepared
