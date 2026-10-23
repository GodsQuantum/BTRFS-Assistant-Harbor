"""Non-writing preview of an ADDITIVE Limine alternate boot entry.

Copies only native, current CachyOS boot image paths and requires matching
kernel modules in the restored root. Never publishes to EFI or selects boot.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from .cachyos_activation_plan import ActivationPlan

_KERNEL = re.compile(r"^linux-cachyos(?:-lts)?$")
_PATH = re.compile(r"^boot\(\):/[A-Za-z0-9._/@:+#%-]{1,319}$")
_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,100}$")
_ROOT = re.compile(r"^  //([A-Za-z0-9._-]+)[ \t]*$")
_FIELD = re.compile(r"^  ([a-z_]+):[ \t]*(\S.*)$")
_HOST = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,62}$")
_CMDLINE = re.compile(r"^[A-Za-z0-9_.,=/:@+% -]+$")
_UUID = re.compile(r"^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$")


@dataclass(frozen=True)
class LimineBootPreview:
    title: str
    menu_addition: str
    selected_kernel_ids: tuple[str, ...]
    existing_configuration_untouched: bool = True
    bootable_certified: bool = False


def preview_recovery_menu(
    existing: str, plan: ActivationPlan, *,
    restored_module_versions: set[str],
    secure_boot_state: str = "unknown",
) -> LimineBootPreview:
    # With Limine secure boot, the EFI binary's config checksum must be
    # enrolled. An additive entry is NOT bootable without native sbctl and
    # checksum enrollment. Unknown state is therefore not safe to publish.
    if secure_boot_state != "disabled":
        raise ValueError("Secure Boot status/enrollment not certified")
    if plan.bootable_certified or not plan.requires_offline_activation:
        raise ValueError("unexpected completed boot certificate")
    if plan.bootloader != "limine" or not _HOST.fullmatch(plan.target_hostname):
        raise ValueError("unsupported recovery bootloader or hostname")
    if len(existing) > 8 * 1024 * 1024 or "\x00" in existing or "\r" in existing:
        raise ValueError("invalid native Limine configuration")
    if not restored_module_versions or len(restored_module_versions) > 128:
        raise ValueError("unknown recovered kernel modules")
    if any(not _VERSION.fullmatch(v) for v in restored_module_versions):
        raise ValueError("unsafe recovered kernel version")
    params = plan.limine_cmdline.split()
    luks = [p.partition("=")[2] for p in params if p.startswith("rd.luks.uuid=")]
    roots = [p.partition("=")[2] for p in params if p.startswith("root=")]
    if (not _CMDLINE.fullmatch(plan.limine_cmdline) or
        len(luks) != 1 or not _UUID.fullmatch(luks[0]) or
        roots != ["/dev/mapper/luks-" + luks[0]] or
        "rootflags=subvol=/@harbor-" + plan.set_id[:8] + "-root" not in params):
        raise ValueError("untrusted target encrypted root command")
    if "\n/+Harbor recovery" in existing:
        raise ValueError("recovery menu already present")
    blocks=[]
    current=None
    in_cachyos=False
    for line in existing.splitlines():
        if line.startswith("/+"):
            if current: blocks.append(current)
            current=None
            in_cachyos=line.strip()=="/+CachyOS"
            continue
        entry=_ROOT.fullmatch(line)
        if entry:
            if current: blocks.append(current)
            current={"kernel_id":entry.group(1),"lines":[]} if in_cachyos else None
            continue
        if current is not None and not line.startswith("     "):
            current["lines"].append(line)
    if current: blocks.append(current)

    names=[]
    entries=[]
    for block in blocks:
        kernel=block["kernel_id"]
        if not _KERNEL.fullmatch(kernel): continue
        fields={}
        for line in block["lines"]:
            m=_FIELD.fullmatch(line)
            if m and m.group(1) in ("path","kernel_path","module_path","cmdline","protocol"):
                if m.group(1) in fields:
                    raise ValueError("duplicate native Limine boot field")
                fields[m.group(1)]=m.group(2).strip()
            if "comment: Kernel version:" in line:
                if "version" in fields:
                    raise ValueError("ambiguous native kernel version")
                fields["version"]=line.partition("Kernel version:")[2].strip()
        version=fields.get("version","")
        if (fields.get("protocol")!="linux" or not _VERSION.fullmatch(version)
            or version not in restored_module_versions):
            continue
        if "path" in fields and "kernel_path" in fields:
            raise ValueError("ambiguous native Limine kernel image path")
        kernel_field = "path" if "path" in fields else "kernel_path"
        for key in (kernel_field,"module_path"):
            path=fields.get(key,"")
            if not _PATH.fullmatch(path) or ".." in path.split("/"):
                raise ValueError("unsafe native Limine image path")
        if "cmdline" not in fields:
            raise ValueError("native kernel boot command missing")
        names.append(kernel)
        entries.append(
            "  //"+plan.target_hostname+"-"+plan.set_id[:8]+"-"+kernel+"\n"
            "  comment: Recovery target "+plan.target_hostname+"\n"
            "  protocol: linux\n"
            "  "+kernel_field+": "+fields[kernel_field]+"\n"
            "  module_path: "+fields["module_path"]+"\n"
            "  cmdline: "+plan.limine_cmdline
        )
    if not entries:
        raise ValueError("no native kernel+initramfs matching recovered modules")
    return LimineBootPreview(
        title="Harbor recovery "+plan.target_hostname,
        menu_addition="/+Harbor recovery\n"+"\n\n".join(entries)+"\n",
        selected_kernel_ids=tuple(names),
    )
