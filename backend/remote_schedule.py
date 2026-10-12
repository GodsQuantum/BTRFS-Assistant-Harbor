#!/usr/bin/env python3
"""Systemd scheduling adapter; Snapper owns snapshots, Harbor owns transfers.

No mounts, Snapper configuration or filesystem sources are ever modified here.
Use only from the explicitly installed and root-reviewed scheduling profile.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

NAMESPACE = uuid.UUID("18e0b70e-dced-4a95-9179-8b45efbd3f51")
FREQUENCIES = {"hourly", "daily", "weekly"}
CONFIG_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}\Z")
SCRIPT_RE = re.compile(r"/[A-Za-z0-9_./-]+\Z")
CONFIG_DIR = Path("/etc/btrfs-assistant-harbor/profiles")
UNIT_DIR = Path("/etc/systemd/system")


@dataclass(frozen=True)
class Profile:
    config: str
    target: str
    frequency: str
    allow_local: bool = False
    engine: str = "checkpoint-v2"
    owner_uid: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.config, str) or CONFIG_RE.fullmatch(self.config) is None:
            raise ValueError("Invalid Snapper config")
        if not isinstance(self.target, str) or not self.target.startswith("/"):
            raise ValueError("Backup destination must be absolute")
        if "\r" in self.target or "\n" in self.target or self.target == "/":
            raise ValueError("Unsafe backup target")
        if os.path.normpath(self.target) != self.target:
            raise ValueError("Backup target has unsafe traversal or trailing separators")
        if self.frequency not in FREQUENCIES:
            raise ValueError("Unsupported systemd schedule")
        if type(self.allow_local) is not bool:
            raise ValueError("allow_local must be boolean")
        if self.engine not in ("checkpoint-v2", "cas"):
            raise ValueError("Unsupported transport engine")
        if self.engine == "cas":
            if type(self.owner_uid) is not int or not 1 <= self.owner_uid <= 65534:
                raise ValueError("CAS schedule needs authenticated non-root desktop UID")
        elif self.owner_uid is not None:
            raise ValueError("legacy schedule does not store owner UID")

    @property
    def profile_id(self) -> str:
        identity = self.config + "\n" + self.target
        if self.engine == "cas":
            identity += "\ncas"
        return str(uuid.uuid5(NAMESPACE, identity))

    def as_dict(self) -> dict:
        payload = {
            "version": 1 if self.engine == "checkpoint-v2" else 2,
            "profile_id": self.profile_id,
            "config": self.config,
            "target": self.target,
            "frequency": self.frequency,
            "allow_local": self.allow_local,
        }
        if self.engine == "cas":
            payload.update(engine="cas", owner_uid=self.owner_uid)
        return payload

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        if not isinstance(data, dict) or data.get("version") not in (1, 2):
            raise ValueError("Unsupported or damaged profile")
        if data["version"] == 1:
            profile = cls(data["config"], data["target"], data["frequency"], data["allow_local"])
        else:
            profile = cls(data["config"], data["target"], data["frequency"],
                          data["allow_local"], data.get("engine"), data.get("owner_uid"))
        if data.get("profile_id") != profile.profile_id:
            raise ValueError("Profile identity does not match stored values")
        return profile


def schedule_argv(profile: Profile, executable: str = "/usr/bin/harbor-checkpoint-v2") -> list[str]:
    return [
        executable, "raw", "checkpoint-v2", "schedule-run",
        "--target", profile.target,
        "--profile-id", profile.profile_id,
        "--snapper-config", profile.config,
        "--name-prefix", "snap-" + profile.config,
        "--experimental",
        *(["--allow-local"] if profile.allow_local else []),
    ]


def service_unit(profile: Profile, script_path: str) -> str:
    if SCRIPT_RE.fullmatch(script_path) is None or ".." in Path(script_path).parts:
        raise ValueError("Unsafe absolute installed backend script path")
    return f"""[Unit]
Description=Btrfs Assistant Harbor remote snapshot transfer {profile.profile_id}
Wants=network-online.target
After=network-online.target remote-fs.target
StartLimitIntervalSec=0

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 {script_path} run --profile-id {profile.profile_id}
Restart=on-failure
RestartSec=60s
NoNewPrivileges=true
TimeoutStartSec=infinity
"""


def timer_unit(profile: Profile, frequency: str) -> str:
    if frequency not in FREQUENCIES:
        raise ValueError("Unsupported schedule")
    return f"""[Unit]
Description=Btrfs Assistant Harbor scheduled send {profile.profile_id}

[Timer]
OnCalendar={frequency}
Persistent=true
RandomizedDelaySec=60s
AccuracySec=1min
Unit=btrfs-assistant-harbor-{profile.profile_id}.service

[Install]
WantedBy=timers.target
"""


def _write_atomic(path: Path, data: bytes) -> None:
    if path.parent.is_symlink() or path.is_symlink():
        raise ValueError("Refusing symlink destination")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / (".tmp-" + uuid.uuid4().hex)
    try:
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            with os.fdopen(fd, "wb") as writer:
                writer.write(data)
                writer.flush()
                os.fsync(writer.fileno())
        except BaseException:
            raise
        os.replace(tmp, path)
        os.chmod(path, 0o600 if path.suffix == ".json" else 0o644)
        dirfd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dirfd)
        finally:
            os.close(dirfd)
    finally:
        tmp.unlink(missing_ok=True)


def install_profile(profile: Profile, config_dir: Path, unit_dir: Path, script_path: str) -> list[Path]:
    prefix = "btrfs-assistant-harbor-" + profile.profile_id
    targets = [
        (config_dir / (profile.profile_id + ".json"), json.dumps(profile.as_dict(), sort_keys=True).encode() + b"\n"),
        (unit_dir / (prefix + ".service"), service_unit(profile, script_path).encode()),
        (unit_dir / (prefix + ".timer"), timer_unit(profile, profile.frequency).encode()),
    ]
    for path, content in targets:
        _write_atomic(path, content)
    return [p for p, _ in targets]


def load_profile(profile_id: str, root: Path = CONFIG_DIR) -> Profile:
    if str(uuid.UUID(profile_id)) != profile_id:
        raise ValueError("Invalid profile id")
    file = root / (profile_id + ".json")
    if file.is_symlink() or file.stat().st_size > 4096:
        raise ValueError("Invalid profile file")
    return Profile.from_dict(json.loads(file.read_text()))


def remove_profile(profile_id: str, config_dir: Path, unit_dir: Path,
                   *, activate: bool = True) -> list[Path]:
    """Disable one profile's timer, then remove only its three own files."""
    profile = load_profile(profile_id, config_dir)
    prefix = f"btrfs-assistant-harbor-{profile.profile_id}"
    paths = [config_dir / f"{profile.profile_id}.json",
             unit_dir / f"{prefix}.service", unit_dir / f"{prefix}.timer"]
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise ValueError("Unsafe or missing schedule profile component")
    if activate:
        subprocess.run(["systemctl", "disable", "--now", f"{prefix}.timer"], check=True)
    for path in paths:
        path.unlink()
    if activate:
        subprocess.run(["systemctl", "daemon-reload"], check=True)
    return paths


def list_profiles(config_dir: Path = CONFIG_DIR) -> list[dict]:
    """Enumerate only recognized, validated profiles, without following symlinks."""
    output = []
    if not config_dir.exists():
        return output
    for file in sorted(config_dir.glob("*.json"))[:1000]:
        if file.is_symlink() or not file.is_file():
            continue
        try:
            profile = load_profile(file.stem, config_dir)
        except (ValueError, OSError, KeyError, TypeError):
            continue
        output.append(profile.as_dict())
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    install = sub.add_parser("install")
    install.add_argument("--snapper-config", required=True)
    install.add_argument("--target", required=True)
    install.add_argument("--frequency", choices=sorted(FREQUENCIES), required=True)
    install.add_argument("--allow-local", action="store_true")
    install.add_argument("--engine", choices=["checkpoint-v2", "cas"], default="checkpoint-v2")
    install.add_argument("--enable", action="store_true")
    run = sub.add_parser("run")
    run.add_argument("--profile-id", required=True)
    remove = sub.add_parser("remove")
    remove.add_argument("--profile-id", required=True)
    sub.add_parser("list")
    args = parser.parse_args(argv)
    if args.action == "list":
        print(json.dumps(list_profiles()))
        return 0
    if args.action == "remove":
        removed = remove_profile(args.profile_id, CONFIG_DIR, UNIT_DIR)
        print(json.dumps({"removed": [str(p) for p in removed]}))
        return 0
    if args.action == "install":
        owner_uid = None
        if args.engine == "cas":
            # Polkit supplies the original desktop UID. Refuse root-only
            # scheduling with ambiguous NFS ownership rather than guessing.
            uid_value = os.environ.get("PKEXEC_UID")
            if uid_value is None or not uid_value.isdecimal():
                raise ValueError("CAS timer requires PKEXEC_UID from Polkit")
            owner_uid = int(uid_value)
        profile = Profile(args.snapper_config, args.target, args.frequency,
                          args.allow_local, args.engine, owner_uid)
        installed = install_profile(profile, CONFIG_DIR, UNIT_DIR, str(Path(__file__).resolve()))
        print(json.dumps({"profile": profile.profile_id, "files": [str(p) for p in installed]}))
        if args.enable:
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "enable", "--now",
                            f"btrfs-assistant-harbor-{profile.profile_id}.timer"], check=True)
        return 0
    profile = load_profile(args.profile_id)
    if profile.engine == "cas":
        from cas_schedule import run_cas_profile
        return run_cas_profile(profile)
    cli = shutil.which("harbor-checkpoint-v2")
    if not cli:
        print("Harbor CLI is missing from the service PATH", file=sys.stderr)
        return 127
    return subprocess.run(schedule_argv(profile, cli), check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
