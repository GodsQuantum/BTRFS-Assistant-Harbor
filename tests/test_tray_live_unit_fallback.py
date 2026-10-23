#!/usr/bin/env python3
import os
from pathlib import Path
import subprocess
import sys
import tempfile

if __name__ == "__main__":
    binary = Path(sys.argv[1]).resolve()
    assert binary.is_file(), binary
    with tempfile.TemporaryDirectory(prefix="harbor-tray-ci-") as work:
        script = Path(work)/"systemctl"
        script.write_text('''#!/bin/sh
    case "$*" in
      *harbor-machine-backup-\\*.service*)
        if [ "$FAKE_HARBOR_MACHINE" = "1" ]; then
          printf 'harbor-machine-backup-00000000-0000-0000-0000-000000000001.service loaded active running example\n'
        fi
        ;;
      *btrfs-assistant-harbor-job@\\*.service*)
        if [ "$FAKE_HARBOR_CAS" = "1" ]; then
          printf 'btrfs-assistant-harbor-job@abc.service loaded active running example\n'
        fi
        ;;
    esac
    exit 0
    ''')
        script.chmod(0o755)
        for machine, cas, expected in ((False,False,"idle"),(True,False,"running"),(False,True,"running"),(True,True,"running")):
            env={**os.environ, "PATH":work+os.pathsep+os.environ.get("PATH",""),
                 "QT_QPA_PLATFORM":"offscreen",
                 "FAKE_HARBOR_MACHINE":str(int(machine)),
                 "FAKE_HARBOR_CAS":str(int(cas))}
            result=subprocess.run([str(binary),"--status"],env=env,
                                  capture_output=True,text=True,timeout=15,check=True)
            assert result.stdout.strip()==expected, (machine,cas,result.stdout,result.stderr)
    print("PASS_TRAY_LIVE_MACHINE_FALLBACK_NO_MONITOR")
