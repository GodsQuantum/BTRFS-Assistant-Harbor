"""Pure, read-only validation/translation for future CachyOS fresh-install restore.

No disk, LUKS, NVRAM, root filesystem or EFI writes occur here.
It plans how the *new* installation's LUKS UUID, machine-id, mounts and
Limine cmdline can be retained while restoring dated Harbor volumes.

Activation is intentionally not enabled: certification requires a real
firmware boot of the recovered system in an isolated UEFI/LUKS2 VM.
"""
from __future__ import annotations
import re
from dataclasses import dataclass

_UUID = re.compile(r"^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$")
_HOST = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,62}$")
_MACHINE_ID = re.compile(r"^[0-9a-f]{32}$")
_MOUNT = re.compile(r"^/(?:[A-Za-z0-9_.@+~-]+/)*[A-Za-z0-9_.@+~-]*$")


@dataclass(frozen=True)
class ActivationPlan:
    set_id: str
    source_hostname: str
    target_hostname: str
    fresh_machine_id: str
    mounts: tuple[tuple[str, str], ...]
    fstab: str
    limine_cmdline: str
    bootloader: str
    bootable_certified: bool = False
    requires_offline_activation: bool = True


def _os_release_is_cachyos(content: str) -> bool:
    for line in content.splitlines():
        if line.startswith("ID="):
            return line.partition("=")[2].strip().strip(chr(34) + chr(39)) == "cachyos"
    return False


def _fstab(content: str) -> dict[str, tuple[str, str, list[str], str]]:
    entries = {}
    for raw in content.splitlines():
        row = raw.split("#", 1)[0].split()
        if not row:
            continue
        if len(row) < 4:
            raise ValueError("truncated fstab record")
        device, mount, fs, options = row[:4]
        if not _MOUNT.fullmatch(mount) or mount in entries:
            raise ValueError("invalid or duplicate fstab mount")
        entries[mount] = (device, fs, options.split(","), raw)
    return entries


def _rewrite_rootflags(cmdline: str, root_subvol: str) -> str:
    """Always preserve NEW installation's encrypted UUID and mapper.

    Never carry the original Pegasus LUKS UUID into a new disk.
    """
    if not root_subvol.startswith("/@harbor-") or not _MOUNT.fullmatch(root_subvol):
        raise ValueError("invalid target root Btrfs subvolume")
    args = cmdline.split()
    luks = [x for x in args if x.startswith("rd.luks.uuid=")]
    root = [x for x in args if x.startswith("root=")]
    if len(luks) != 1 or len(root) != 1 or not _UUID.fullmatch(luks[0].split("=", 1)[1]):
        raise ValueError("fresh installation has no single LUKS2 root identity")
    expected = "/dev/mapper/luks-" + luks[0].split("=", 1)[1]
    if root[0].split("=", 1)[1] != expected:
        raise ValueError("root mapper and current LUKS UUID do not match")
    flags = [x for x in args if x.startswith("rootflags=")]
    if len(flags) != 1:
        raise ValueError("fresh Limine rootflags missing or ambiguous")
    options = flags[0].split("=", 1)[1].split(",")
    subvols = [part for part in options if part.startswith("subvol=") or
               part.startswith("subvolid=")]
    if len(subvols) != 1:
        raise ValueError("fresh Limine entry has ambiguous root subvolume")
    replaced = ["subvol=" + root_subvol if part in subvols else part for part in options]
    return " ".join("rootflags=" + ",".join(replaced) if item == flags[0] else item for item in args)


def plan_cachyos_activation(
    catalog: dict,
    *,
    source_os_release: str,
    fresh_os_release: str,
    source_fstab: str,
    fresh_fstab: str,
    fresh_limine_cmdline: str,
    fresh_machine_id: str,
    current_hostname: str,
    hostname_policy: str,
    custom_hostname: str = "",
) -> ActivationPlan:
    """Pure reproducible recovery plan; NO write/format/mount/reboot actions."""
    set_id = catalog.get("set_id")
    if not isinstance(set_id, str) or not _UUID.fullmatch(set_id):
        raise ValueError("missing canonical machine-set UUID")
    if catalog.get("status") != "completed_btrfs_and_boot_files":
        raise ValueError("entire computer backup (Btrfs plus EFI) required")
    if catalog.get("bootable") is not False:
        raise ValueError("untrusted machine-set bootable flag")
    if not (_os_release_is_cachyos(source_os_release) and
            _os_release_is_cachyos(fresh_os_release)):
        raise ValueError("CachyOS source and fresh target are both required")
    machine = catalog.get("machine_name")
    if not isinstance(machine, str) or not _HOST.fullmatch(machine):
        raise ValueError("original computer hostname invalid")
    if not _HOST.fullmatch(current_hostname):
        raise ValueError("fresh installation hostname invalid")
    if hostname_policy not in ("original", "installed", "custom"):
        raise ValueError("unknown hostname recovery policy")
    new_hostname = (machine if hostname_policy == "original" else
                    current_hostname if hostname_policy == "installed" else
                    custom_hostname)
    if not _HOST.fullmatch(new_hostname):
        raise ValueError("new computer hostname invalid")
    if not _MACHINE_ID.fullmatch(fresh_machine_id):
        raise ValueError("fresh machine-id missing or invalid")

    members = catalog.get("members")
    boots = catalog.get("boot_members")
    if not isinstance(members, list) or not members:
        raise ValueError("missing Btrfs system sources")
    mounts = []
    seen = set()
    for entry in members:
        mount = entry.get("original_mount") if isinstance(entry, dict) else None
        if (not isinstance(mount, str) or not _MOUNT.fullmatch(mount)
                or mount in seen or entry.get("status") != "completed"):
            raise ValueError("invalid/missing/duplicate backed-up Btrfs mount")
        seen.add(mount)
        mounts.append(mount)
    if "/" not in seen or "/home" not in seen:
        raise ValueError("whole-computer backup must cover / and /home")
    if not isinstance(boots, list) or len(boots) != 1:
        raise ValueError("exactly one verified EFI partition required")
    boot = boots[0]
    if (boot.get("mount_point") != "/boot" or
            boot.get("filesystem") != "vfat" or
            boot.get("status") != "completed"):
        raise ValueError("fresh CachyOS Limine requires verified FAT32 /boot")

    old = _fstab(source_fstab)
    new = _fstab(fresh_fstab)
    for mount in mounts:
        # Nested Btrfs subvolumes need not have an fstab entry: for example
        # /var/lib/machines and /var/lib/portables can be discovered as real
        # subvolume roots inside @ and archived independently. The verified
        # catalog is authoritative for those nested sources. Reject an
        # explicit source fstab that contradicts their Btrfs identity.
        if mount not in old:
            if mount in ("/", "/home"):
                raise ValueError("source Btrfs system mount absent from original fstab: " + mount)
            continue
        if old[mount][1] != "btrfs":
            raise ValueError("source Btrfs subvolume contradicts original fstab: " + mount)
    if "/boot" not in old or old["/boot"][1] != "vfat":
        raise ValueError("source has no EFI fstab entry")
    if "/" not in new or new["/"][1] != "btrfs":
        raise ValueError("fresh installation root must be Btrfs")
    if "/boot" not in new or new["/boot"][1] != "vfat":
        raise ValueError("fresh installation must mount its own VFAT EFI at /boot")
    target_root_device = new["/"][0]
    luks_ids = [
        field.split("=", 1)[1]
        for field in fresh_limine_cmdline.split()
        if field.startswith("rd.luks.uuid=")
    ]
    if len(luks_ids) != 1 or not _UUID.fullmatch(luks_ids[0]):
        raise ValueError("fresh Limine LUKS UUID missing or ambiguous")
    luks_id = luks_ids[0]
    # CachyOS supports both a filesystem UUID and a LUKS mapper in fstab.
    # Retain the freshly installed identity verbatim; never substitute an
    # old computer's mapper or UUID.
    if not (
        re.fullmatch(r"UUID=[0-9a-f-]{36}", target_root_device)
        or target_root_device == "/dev/mapper/luks-" + luks_id
    ):
        raise ValueError("fresh root has no verified new filesystem identity")
    for mount in new:
        if (mount not in mounts and mount != "/boot" and
                new[mount][1] not in ("swap", "tmpfs", "proc", "sysfs", "devpts") and
                "noauto" not in new[mount][2]):
            raise ValueError("unprotected new installation persistent mount: " + mount)
    for mount in mounts:
        if mount in new and new[mount][1] != "btrfs":
            raise ValueError("source/target filesystem mismatch: " + mount)

    # Each recovered volume gets a separate, collision-free Btrfs subvolume
    # without renaming or deleting the fresh install's active @/@home.
    suffix = set_id[:8]
    remap = {mount: "/@harbor-" + suffix + ("-root" if mount == "/" else
              "-" + mount.strip("/").replace("/", "-")) for mount in mounts}
    preserved = []
    for raw in fresh_fstab.splitlines():
        parts = raw.split("#", 1)[0].split()
        if len(parts) >= 4 and parts[1] in remap:
            options = [x for x in parts[3].split(",") if not x.startswith(
                ("subvol=", "subvolid="))]
            options.append("subvol=" + remap[parts[1]])
            new_record = parts[:]
            new_record[3] = ",".join(options)
            preserved.append(" ".join(new_record))
        else:
            preserved.append(raw)
    for mount in sorted(set(mounts) - set(new), key=lambda v: (v.count("/"), v)):
        preserved.append(
            f"{target_root_device} {mount} btrfs defaults,subvol={remap[mount]} 0 0")
    cmdline = _rewrite_rootflags(fresh_limine_cmdline, remap["/"])
    return ActivationPlan(
        set_id=set_id,
        source_hostname=machine,
        target_hostname=new_hostname,
        fresh_machine_id=fresh_machine_id,
        mounts=tuple((mount, remap[mount]) for mount in sorted(mounts)),
        fstab="\n".join(preserved) + "\n",
        limine_cmdline=cmdline,
        bootloader="limine",
    )
