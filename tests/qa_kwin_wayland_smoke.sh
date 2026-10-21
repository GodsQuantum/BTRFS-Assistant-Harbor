#!/usr/bin/env bash
# Real KWin virtual Wayland compositor smoke, fully isolated with its own D-Bus.
# Test-owned runtime directory and socket; never touches the desktop session.
set -euo pipefail
build="build/ci"
if (( $# > 0 )); then build="$1"; fi
command -v kwin_wayland >/dev/null || { echo "kwin_wayland missing"; exit 42; }
command -v dbus-run-session >/dev/null || { echo "dbus-run-session missing"; exit 42; }
runtime="$(mktemp -d /tmp/harbor-kwin-XXXXXX)"
chmod 0700 "$runtime"
trap 'rm -rf "$runtime"' EXIT
export XDG_RUNTIME_DIR="$runtime"
export LIBGL_ALWAYS_SOFTWARE=1
export HARBOR_BUILD_DIR="$build"
dbus-run-session -- bash -c '
  set -euo pipefail
  export XDG_RUNTIME_DIR="$1" LIBGL_ALWAYS_SOFTWARE=1
  kwin_wayland --virtual --width 1280 --height 800 --socket harbor-kwin \
    --no-lockscreen --no-global-shortcuts > "$1/kwin.log" 2>&1 &
  kwpid=$!
  trap "kill $kwpid 2>/dev/null || true; wait $kwpid 2>/dev/null || true" EXIT
  ready=0
  for i in $(seq 1 60); do
    if test -S "$1/harbor-kwin"; then ready=1; break; fi
    if ! kill -0 "$kwpid" 2>/dev/null; then break; fi
    sleep 0.2
  done
  if test "$ready" != 1; then
    tail -55 "$1/kwin.log"
    echo "KWIN_WAYLAND_QA_COMPOSITOR_FAILED" >&2
    exit 43
  fi
  echo "KWIN_COMPOSITOR_VERSION=$(kwin_wayland --version)"
  env QT_QPA_PLATFORM=wayland WAYLAND_DISPLAY=harbor-kwin \
    ctest --test-dir "$HARBOR_BUILD_DIR" -R "^gui-user-workflow-smoke$" --output-on-failure
' bash "$runtime"
echo "PASS_KWIN_WAYLAND_GUI_SMOKE_NOT_FULL_PLASMA_SESSION"
