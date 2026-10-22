#!/usr/bin/env python3
"""Build an Ubuntu 26.04 preview DEB from an already tested CMake build.

Does NOT modify /, /etc, Snapper or any mounted volume.
Distribution-native rebuilds should use the source package.
"""
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
import shutil
import subprocess

VERSION = "0.1.1-1"

def call(*args: str, cwd: Path | None = None, env: dict | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, env=env, check=True,
                            capture_output=True, text=True)
    return result.stdout

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=VERSION,
                        help="Debian package version, optionally suffixed for target distro")
    parser.add_argument("--build", required=True, type=Path,
                        help="verified Qt/CMake build directory")
    parser.add_argument("--out", required=True, type=Path,
                        help="empty disposable release output directory")
    args = parser.parse_args()
    if not re.fullmatch(rf"{re.escape(VERSION)}(?:[+][A-Za-z0-9.]+)?", args.version):
        parser.error("unsafe or incompatible version")
    project = Path(__file__).resolve().parents[2]
    build = args.build.resolve()
    out = args.out.resolve()
    assert build.is_dir() and (build / "CMakeCache.txt").is_file()
    assert out != Path("/") and not out.is_symlink()
    if out.exists():
        assert not any(out.iterdir()), "Output directory must be empty"
    out.mkdir(parents=True, exist_ok=True)
    stage = out / "root"
    stage.mkdir()
    env = os.environ.copy()
    env["DESTDIR"] = str(stage)
    call("cmake", "--install", str(build), "--prefix", "/usr", env=env)
    gui = stage / "usr/bin/btrfs-assistant-harbor-bin"
    rust = stage / "usr/bin/harbor-transport"
    rescue = stage / "usr/lib/btrfs-harbor/recovery/harbor-rear-restore"
    assert gui.is_file() and rust.is_file() and rescue.is_file()
    assert "0.1.1" in call(str(gui), "--version") and "alpha" not in call(str(gui), "--version")
    call("bash", "-n", str(rescue))
    doc = stage / "usr/share/doc/btrfs-assistant-harbor"
    doc.mkdir(parents=True, exist_ok=True)
    shutil.copy2(project / "LICENSE", doc / "copyright")
    shutil.copy2(project / "README.md", doc / "README.md")
    shutil.copy2(project / "README.fr.md", doc / "README.fr.md")
    for name in ("UTILISATION_FR.md", "RECUPERATION_REAR_FR.md"):
        shutil.copy2(project / "docs/guides" / name, doc / name)
    # dpkg-shlibdeps resolves runtime linker dependencies on the build distro.
    check = out / "shlibs"
    (check / "debian").mkdir(parents=True)
    (check / "debian/control").write_text(
        "Source: btrfs-assistant-harbor\nSection: admin\nPriority: optional\n"
        "Maintainer: Btrfs Assistant Harbor community <noreply@github.com>\n"
        "Standards-Version: 4.6.2\n\n"
        "Package: btrfs-assistant-harbor\nArchitecture: any\nDescription: Btrfs Assistant Harbor Linux backup release\n"
    )
    dynamic = call("dpkg-shlibdeps", "-O", "-e" + str(gui),
                   "-e" + str(rust), cwd=check).strip()
    assert dynamic.startswith("shlibs:Depends="), dynamic
    deps = dynamic.split("=", 1)[1] + (
        ", btrfs-progs, snapper, polkitd, pkexec, python3, "
        "python3-filelock, python3-rich, zstd"
    )
    control = stage / "DEBIAN/control"
    control.parent.mkdir()
    # Shared NVMe staging inherits setgid; dpkg-deb requires DEBIAN <=0775.
    control.parent.chmod(0o755)
    control.write_text(
        "Package: btrfs-assistant-harbor\n"
        f"Version: {args.version}\n"
        "Section: admin\nPriority: optional\nArchitecture: amd64\n"
        "Maintainer: Btrfs Assistant Harbor community <noreply@github.com>\n"
        f"Depends: {deps}\n"
        "Description: Btrfs Assistant fork with Harbor CAS and ReaR rescue integration\n"
        " Linux x86-64 stable scope. Local Snapper features are inherited from\n"
        " upstream; UEFI recovery is qualified only on the documented VM profile.\n"
    )
    target = out / f"btrfs-assistant-harbor_{args.version}_amd64.deb"
    call("dpkg-deb", "--root-owner-group", "--build", str(stage), str(target))
    print("BUILT", target, "bytes", target.stat().st_size)
    print("DEPENDENCIES", deps)
    call("dpkg-deb", "--info", str(target))
    call("dpkg-deb", "--contents", str(target))

if __name__ == "__main__":
    main()
