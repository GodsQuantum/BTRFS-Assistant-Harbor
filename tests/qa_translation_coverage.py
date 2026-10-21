#!/usr/bin/env python3
"""Verify active Harbor Qt remote-backup strings are translated in FR and zh_CN.

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

def context_messages(path: Path) -> dict[str, ET.Element]:
    ts = ET.parse(path)
    contexts = [c for c in ts.findall("context") if c.findtext("name") == CONTEXT]
    if len(contexts) != 1:
        raise RuntimeError(f"{path} has {len(contexts)} {CONTEXT} contexts")
    return {
        m.findtext("source"): m for m in contexts[0].findall("message")
        if m.findtext("source")
    }

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
            tool, str(ROOT / "src/ui/RemoteBackupWidget.cpp"),
            "-locations", "none", "-ts", str(reference),
        ], check=True, capture_output=True, text=True)
        source = context_messages(reference)
        if len(source) < 133:
            raise RuntimeError(f"Unexpected Qt message inventory count {len(source)}")
        result = {}
        for lang in ("fr_FR", "zh_CN"):
            translations = context_messages(ROOT / f"translations/btrfsassistant_{lang}.ts")
            missing = []
            bad = []
            for english in source:
                message = translations.get(english)
                translation = message.find("translation") if message is not None else None
                translated = (
                    (translation.text or "") if translation is not None
                    else ""
                )
                if not translated.strip() or translation.get("type") == "unfinished":
                    missing.append(english)
                elif Counter(PLACEHOLDER.findall(english)) != Counter(PLACEHOLDER.findall(translated)):
                    bad.append(english)
            if missing or bad:
                raise RuntimeError(
                    f"{lang}: {len(missing)} missing/unfinished and {len(bad)} unsafe placeholders: "
                    f"missing={missing[:6]!r}, invalid={bad[:6]!r}"
                )
            result[lang] = {
                "covered": len(source),
                "missing": 0,
                "unsafe_placeholders": 0,
            }
        print("HARBOR_QT_LOCALIZATION_PASS", json.dumps(result, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    main()
