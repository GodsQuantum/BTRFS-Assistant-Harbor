#!/usr/bin/env python3
"""Verify the complete Harbor Qt desktop (not only the remote tab) in FR and zh_CN.

Use Qt's own lupdate parser rather than a regex over C++ string literals.
Do not mutate tracked TS catalogs or mark untranslated safety messages as PASS.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CONTEXT = "RemoteBackupWidget"
PLACEHOLDER = re.compile(r"%[1-9][0-9]*")

def all_messages(path: Path) -> dict[tuple[str, str], ET.Element]:
    tree = ET.parse(path)
    result: dict[tuple[str, str], ET.Element] = {}
    for context in tree.findall("context"):
        name = context.findtext("name") or ""
        for message in context.findall("message"):
            english = message.findtext("source")
            if english:
                result[(name, english)] = message
    return result


def main() -> None:
    tool = next((
        p for p in (
            shutil.which("lupdate"), shutil.which("lupdate-qt6"),
            "/usr/lib/qt6/bin/lupdate", "/usr/lib64/qt6/bin/lupdate",
        ) if p and Path(p).is_file()
    ), None)
    if tool is None:
        raise RuntimeError("Qt6 lupdate missing: cannot certify translations")
    with tempfile.TemporaryDirectory(prefix="harbor-l10n-") as tmp:
        reference = Path(tmp) / "reference.ts"
        subprocess.run([
            tool, str(ROOT / "src"),
            "-locations", "none", "-ts", str(reference),
        ], check=True, capture_output=True, text=True)
        source = all_messages(reference)
        if len(source) < 410:
            raise RuntimeError(f"Unexpected full GUI Qt message inventory count {len(source)}")
        remote = {key for key in source if key[0] == "RemoteBackupWidget"}
        if len(remote) < 136:
            raise RuntimeError(f"Unexpected remote backup inventory {len(remote)}")
        result = {}
        for lang in ("fr_FR", "zh_CN"):
            translations = all_messages(ROOT / f"translations/btrfsassistant_{lang}.ts")
            missing = []
            bad = []
            for key in source:
                message = translations.get(key)
                translation = message.find("translation") if message is not None else None
                translated = translation.text or "" if translation is not None else ""
                if not translated.strip() or translation.get("type") == "unfinished":
                    missing.append(key)
                elif Counter(PLACEHOLDER.findall(key[1])) != Counter(PLACEHOLDER.findall(translated)):
                    bad.append(key)
            if missing or bad:
                raise RuntimeError(
                    f"{lang}: {len(missing)} missing/unfinished and {len(bad)} unsafe placeholders: "
                    f"missing={missing[:8]!r}, invalid={bad[:8]!r}"
                )
            result[lang] = {
                "gui_messages": len(source),
                "remote_messages": len(remote),
                "missing": 0,
                "unsafe_placeholders": 0,
            }
        print("HARBOR_QT_LOCALIZATION_PASS", json.dumps(result, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    main()
