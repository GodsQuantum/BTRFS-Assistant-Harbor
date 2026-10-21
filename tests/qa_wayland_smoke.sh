#!/usr/bin/env bash
set -euo pipefail
# Headless Wayland: verifies GUI navigation on Wayland, not KDE Plasma parity.
build="build/ci"
if (( $# > 0 )); then build="$1"; fi
runtime="$(mktemp -d /tmp/harbor-wayland-XXXXXX)"
chmod 0700 "$runtime"
export XDG_RUNTIME_DIR="$runtime"
compositor_pid=""
cleanup() {
  if [[ -n "$compositor_pid" ]]; then
    kill "$compositor_pid" 2>/dev/null || true
    wait "$compositor_pid" 2>/dev/null || true
  fi
  rm -rf "$runtime"
}
trap cleanup EXIT
weston --backend=headless-backend.so --socket=harbor-qa --idle-time=0 \
  --log="$runtime/weston.log" >/dev/null 2>&1 &
compositor_pid=$!
ready=0
for _ in {1..50}; do
  if [[ -S "$runtime/harbor-qa" ]]; then ready=1; break; fi
  if ! kill -0 "$compositor_pid" 2>/dev/null; then break; fi
  sleep 0.2
done
if [[ "$ready" != 1 ]]; then
  cat "$runtime/weston.log"
  echo "G09_QA_WAYLAND_COMPOSITOR_FAILED" >&2
  exit 40
fi
echo "WAYLAND_COMPOSITOR=$(weston --version)"
QT_QPA_PLATFORM=wayland WAYLAND_DISPLAY=harbor-qa \
  ctest --test-dir "$build" -R '^gui-user-workflow-smoke$' --output-on-failure
echo "PASS_QT_GUI_WAYLAND_HEADLESS_NOT_KDE_PLASMA"
